
import copy
import traceback
from queue import Queue
from time import sleep
from logging import INFO
from datetime import datetime, time
from collections import OrderedDict

from paper_trading.event import Event
from paper_trading.utility.event import (
    EVENT_ERROR,
    EVENT_LOG,
    EVENT_MARKET_CLOSE
)
from paper_trading.utility.setting import SETTINGS
from paper_trading.api.pytdx_api import PYTDXService
from paper_trading.trade.account import (
    on_order_deal,
    on_order_cancel,
    on_order_refuse,
    order_generate,
    query_orders_today,
    query_account_list,
    query_position,
    on_position_update_price,
    on_liquidation
)
from paper_trading.utility.model import Order, DBData, Status, LogData
from paper_trading.utility.constant import OrderType, PriceType, TradeType


class Exchange:
    """
    交易所类
    1、其他所有交易市场需要继承此类；
    2、必须重写on_match、on_orders_arrived，verification_register
    """

    def __init__(self, event_engine):
        self.market_name = ""              # 市场名称
        self._active = False
        self.event_engine = event_engine   # 事件引擎

        self.hq_client = None              # 行情源
        self.db = None                     # 数据库实例
        self.period = SETTINGS["PERIOD"]   # 撮合效率，单位秒
        self.exchange_symbols = []         # 交易市场标识
        self.turnover_mode = None          # 回转交易模式
        self.verification = OrderedDict()  # 验证清单
        self.orders_book = OrderedDict()   # 订单薄

    def on_init(self):
        """初始化"""
        # 开启交易撮合开关
        self._active = True

        # 绑定交易市场名称，用于订单薄接收订单
        SETTINGS["MARKET_NAME"] = self.market_name

        # 注册验证程序
        self.verification_register()

        # 返回订单接收函数
        return self.on_orders_arrived

    def on_match(self, db):
        """订单撮合"""
        pass

    def on_orders_arrived(self, order):
        """订单到达"""
        pass

    def on_orders_match(self, order: Order):
        """订单撮合"""
        try:
            hq = self.hq_client.get_realtime_data(order.pt_symbol)

            if len(hq):
                ask1 = float(hq.loc[0, "ask1"])
                bid1 = float(hq.loc[0, 'bid1'])

                if order.order_type == OrderType.BUY.value:
                    # 涨停
                    if ask1 == 0:
                        return
                    # 市价委托即时成交
                    if order.price_type == PriceType.MARKET.value:
                        order.order_price = ask1
                        order.trade_price = ask1
                        self.on_order_deal(order)
                        return True
                    # 限价委托
                    elif order.price_type == PriceType.LIMIT.value:
                        if order.order_price >= ask1:
                            order.trade_price = ask1
                            # 订单成交
                            self.on_order_deal(order)
                            return True
                else:
                    # 跌停
                    if bid1 == 0:
                        return
                    # 市价委托即时成交
                    if order.price_type == PriceType.MARKET.value:
                        order.order_price = bid1
                        order.trade_price = bid1
                        self.on_order_deal(order)
                        return True
                    # 限价委托
                    elif order.price_type == PriceType.LIMIT.value:
                        if order.order_price <= bid1:
                            order.trade_price = bid1
                            # 订单成交
                            self.on_order_deal(order)
                            return True
        except Exception as e:
            self.write_log(traceback.format_exc())
            return False

    def on_order_deal(self, order: Order):
        """订单成交"""
        order.traded = order.volume
        order.trade_type = self.turnover_mode

        on_order_deal(order, self.db)

    def on_order_status_modify(self, order):
        """更新订单信息"""
        raw_data = {}
        raw_data['flt'] = {'order_id': order.order_id}
        raw_data["set"] = {'$set': {'status': order.status}}
        db_data = DBData(
            db_name=SETTINGS['TRADE_DB'],
            db_cl=self.market_name,
            raw_data=raw_data
        )

        return self.db.on_update(db_data)

    def load_orders_today(self):
        """查询当日未成交的订单"""
        account_list = query_account_list(self.db)

        for account_id in account_list:
            orders = query_orders_today(account_id, self.db)
            if isinstance(orders, list):
                for order in orders:
                    if order['status'] in [ Status.SUBMITTING.value,
                                            Status.NOTTRADED.value,
                                            Status.PARTTRADED.value]:
                        order = order_generate(order)
                        self.orders_book[order.order_id] = order

        self.write_log(f"加载未处理订单共计：{str(len(self.orders_book))}条")

    def on_rejected_all(self):
        """拒绝所有订单"""
        if self.orders_book:
            for order in self.orders_book.values():
                order.status = Status.REJECTED.value
                order.error_msg = "交易关闭，自动拒单"

                on_order_refuse(order, self.db)

                self.write_log(
                    "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                        order.account_id,
                        order.order_id,
                        order.error_msg))

    def liquidation(self):
        """收盘清算"""
        tokens = query_account_list(self.db)
        today = datetime.now().strftime("%Y%m%d")

        if tokens:
            for token in tokens:
                pos_list = query_position(token, self.db)
                if isinstance(pos_list, list):
                    for pos in pos_list:
                        hq = self.hq_client.get_realtime_data(pos["pt_symbol"])
                        if hq is not None:
                            now_price = float(hq.loc[0, "price"])
                            # 更新收盘行情
                            on_position_update_price(token, pos, now_price, self.db)
                # 清算
                on_liquidation(self.db, token, today)
        self.write_log("{}: 账户与持仓清算完成".format(self.market_name))

    def on_close(self):
        """模拟交易市场关闭"""
        # 阻止接收新订单
        SETTINGS["MARKET_NAME"] = ""

        # 关闭市场撮合
        self._active = False

        # 模拟交易结束，拒绝所有未成交的订单
        self.on_rejected_all()

        # 清算
        self.liquidation()

        # 关闭行情接口
        self.hq_client.close()

        # 推送关闭事件
        event = Event(EVENT_MARKET_CLOSE, self.market_name)
        self.event_engine.put(event)

    """订单验证"""

    def verification_register(self):
        """验证注册"""
        pass

    def time_verification(self):
        """交易时间验证"""
        result = False
        now = datetime.now().time()
        time_dict = {
            "1": (time(9, 15), time(11, 30)),
            "2": (time(13, 0), time(15, 0))
        }
        for k, time_check in time_dict.items():
            if (now >= time_check[0] and now <= time_check[1]):
                result = True

        if now >= time(15, 0):
            # 市场关闭
            self.on_close()

        return result

    def product_verification(self, order: Order):
        """交易产品验证"""
        if order.exchange in self.exchange_symbols:
            return True, ""
        else:
            return False, "交易品种不符"

    def price_verification(self, order: Order):
        """价格验证"""
        return True, ""

    def on_back_verification(self, order: Order):
        """后端验证"""
        for k, verification in self.verification.items():
            result, msg = verification(order)

            if not result:
                order.status = Status.REJECTED.value
                order.error_msg = msg
                on_order_refuse(order, self.db)

                self.write_log(
                    "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                        order.account_id, order.order_id, msg))

                return False

        return True

    def write_log(self, msg: str, level: int = INFO):
        """"""
        log = LogData(
            log_content=msg,
            log_level=level
        )
        event = Event(EVENT_LOG, log)
        self.event_engine.put(event)


class BacktestMarket(Exchange):
    """
    回测数据模拟交易市场
    1、即时按委托价格成交；
    2、接收清算订单后清算数据；
    3、为保证数据准确，使用订单队列接收和处理订单
    """

    def __init__(self, event_engine):
        super(BacktestMarket, self).__init__(event_engine)

        self.market_name = "backtest_market"            # 交易市场名称
        self.turnover_mode = TradeType.T_PLUS1.value    # 交收类型
        self.orders_queue = Queue()                     # 使用订单队列

    def on_match(self, db):
        """交易撮合"""
        self.db = db
        self.write_log("{}：交易市场已开启".format(self.market_name))

        try:
            while self._active:
                if self.orders_queue.empty():
                    continue

                order = self.orders_queue.get(block=True)

                # 模拟清算
                if order.order_type == OrderType.LIQ.value:
                    on_liquidation(
                        self.db,
                        order.account_id,
                        order.order_date,
                        {order.pt_symbol: order.order_price}
                    )
                    continue

                # 订单成交
                # 回测使用委托价格作为成交价格
                order.trade_price = order.order_price
                self.on_order_deal(order)

        except Exception as e:
            event = Event(EVENT_ERROR, traceback.format_exc())
            self.event_engine.put(event)

    def on_orders_arrived(self, order):
        """订单到达-回测模式"""
        # 过滤掉取消订单
        if order.order_type == OrderType.CANCEL.value:
            return False

        # 订单验证
        if not self.on_back_verification(order):
            return False

        # 订单推送到订单撮合引擎
        self.orders_queue.put(order)


class ChinaAMarket(Exchange):
    """中国A股交易市场"""

    def __init__(self, event_engine):
        super(ChinaAMarket, self).__init__(event_engine)

        self.market_name = "china_a_market"            # 交易市场名称
        self.hq_client = PYTDXService()                # 行情源
        self.exchange_symbols = ["SH", "SZ"]           # 交易市场标识
        self.turnover_mode = TradeType.T_PLUS1.value   # 回转交易模式

    def on_match(self, db):
        """交易撮合"""
        self.db = db
        self.write_log("{}：交易市场已开启".format(self.market_name))
        try:
            # 行情连接
            self.hq_client.connect_api()

            # 加载当日未成交的订单
            self.load_orders_today()

            while self._active:
                # 交易时间检验
                if not self.time_verification():
                    continue

                if not self.orders_book:
                    continue

                # 复制交易簿
                orders = copy.copy(self.orders_book)
                for order_id, order in orders.items():
                    sleep(1)
                    # 订单撮合
                    if self.on_orders_match(order):
                        del self.orders_book[order_id]

        except Exception as e:
            event = Event(EVENT_ERROR, traceback.format_exc())
            self.event_engine.put(event)

    def on_orders_arrived(self, order):
        """订单到达-真实行情"""
        order_id = order.order_id

        # 取消订单的处理
        if order.order_type == OrderType.CANCEL.value:
            if self.orders_book.get(order_id):
                del self.orders_book[order_id]
                on_order_cancel(order.account_id, order_id, self.db)
                return True
            else:
                return False
        # 过滤掉清算订单
        elif order.order_type == OrderType.LIQ.value:
            return False
        else:
            # 订单验证
            if not self.on_back_verification(order):
                # 验证失败拒单
                on_order_refuse(order, self.db)
            else:
                # 更新订单状态及信息
                order.status = Status.NOTTRADED.value
                self.on_order_status_modify(order)
                self.write_log(f"收到订单:{order_id}")
                # 将订单添加到订单薄
                self.orders_book[order_id] = order
                return True

    def verification_register(self):
        """验证注册"""
        self.verification = {
            "1": self.product_verification,
            "2": self.price_verification,
        }
