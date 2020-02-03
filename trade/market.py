
from time import sleep
from queue import Queue
from logging import INFO
from datetime import datetime, time
from collections import OrderedDict

from paper_trading.event import Event
from paper_trading.utility.event import (
    EVENT_ERROR,
    EVENT_LOG,
    EVENT_MARKET_CLOSE,
    EVENT_ORDER_DEAL,
    EVENT_ORDER_REJECTED,
    EVENT_ORDER_CANCELED
)
from paper_trading.utility.setting import SETTINGS
from paper_trading.api.tushare_api import TushareService
from paper_trading.trade.account import (
    order_generate,
    query_orders_today,
    query_account_list,
    query_position,
    on_position_update_price,
    on_liquidation
)
from paper_trading.utility.model import Order, DBData, Status, LogData
from paper_trading.utility.constant import OrderType, PriceType, TradeType, EngineMode


class Exchange(object):
    """交易所"""

    def __init__(self, event_engine, mode):
        self.market_name = ""              # 市场名称
        self._active = False
        self.event_engine = event_engine   # 事件引擎
        self.hq_client = None              # 行情源
        self.db = None                     # 数据库实例
        self.match_mode = mode             # 模拟交易引擎类型
        self.period = SETTINGS["PERIOD"]   # 撮合效率，单位秒
        self.exchange_symbols = []         # 交易市场标识
        self.turnover_mode = None          # 回转交易模式
        # 真实环境下使用订单薄
        self.orders_book = OrderedDict()
        # 模拟环境下使用订单队列
        self.orders_queue = Queue()

    def on_match(self, db):
        """"""
        pass

    def on_realtime_match(self):
        """实时交易撮合"""
        pass

    def on_simulation_match(self):
        """模拟交易撮合"""
        pass

    def on_close(self):
        """市场关闭"""
        pass

    def liquidation(self):
        """清算"""


class ChinaAMarket(Exchange):
    """中国A股交易市场"""

    def __init__(self, event_engine, mode):
        super(ChinaAMarket, self).__init__(event_engine, mode)

        self.market_name = "china_a_market"            # 交易市场名称
        self._active = False
        self.hq_client = TushareService()              # 行情源
        self.db = None                                 # 数据库实例
        self.exchange_symbols = ["SH", "SZ"]           # 交易市场标识
        self.match_mode = mode                         # 模拟交易引擎类型
        self.turnover_mode = TradeType.T_PLUS1.value   # 回转交易模式
        self.verification = OrderedDict()              # 验证清单
        # 真实环境下使用订单薄
        self.orders_book = OrderedDict()
        # 模拟环境下使用订单队列
        self.orders_queue = Queue()

    def on_init(self):
        """初始化"""
        # 开启交易撮合开关
        self._active = True

        # 绑定交易市场名称，用于订单薄接收订单
        SETTINGS["MARKET_NAME"] = self.market_name

        # 注册验证程序
        if self.match_mode == EngineMode.REALTIME.value:
            self.verification = {
                "1": self.product_verification,
                "2": self.price_verification,
            }
            return self.on_orders_arrived_realtime

        else:
            self.verification = {
                "1": self.product_verification,
            }
            return self.on_orders_arrived_simulation

    def on_match(self, db):
        """交易撮合"""
        self.db = db
        self.write_log("{}：交易市场已开启".format(self.market_name))

        try:
            if self.match_mode == EngineMode.REALTIME.value:
                self.on_realtime_match()
            else:
                self.on_simulation_match()

        except Exception as e:
            event = Event(EVENT_ERROR, e)
            self.event_engine.put(event)

    def on_realtime_match(self):
        """实时交易撮合"""
        self.write_log("{}：真实行情".format(self.market_name))

        # 行情连接
        self.hq_client.connect_api()

        # 加载当日未成交的订单
        self.load_orders_today_notrade()

        while self._active:
            # 交易时间检验
            if not self.time_verification():
                continue

            if not self.orders_book:
                continue

            for order in self.orders_book.values():
                # 订单撮合
                self.on_orders_match(order)
            sleep(3)

    def on_simulation_match(self):
        """模拟交易撮合"""
        self.write_log("{}：模拟行情".format(self.market_name))

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
            self.on_orders_deal(order)

    def on_orders_arrived_realtime(self, order):
        """订单到达-真实行情"""
        order_id = order.order_id

        # 取消订单的处理
        if order.order_type == OrderType.CANCEL.value:
            if self.orders_book.get(order_id):
                del self.orders_book[order_id]
                self.on_order_canceled(order.account_id, order_id)
                return True
            else:
                return False
        # 过滤掉清算订单
        elif order.order_type == OrderType.LIQ.value:
            return False
        else:
            # 订单验证
            if not self.on_back_verification(order):
                return False
            else:
                # 将订单添加到订单薄
                self.orders_book[order_id] = order
                return True

    def on_orders_arrived_simulation(self, order):
        """订单到达-模拟行情"""
        # 过滤掉取消订单
        if order.order_type == OrderType.CANCEL.value:
            return False

        # 订单验证
        if not self.on_back_verification(order):
            return False

        # 订单推送到订单撮合引擎
        self.orders_queue.put(order)
        return True

    def on_orders_match(self, order: Order):
        """订单撮合"""
        hq = self.hq_client.get_realtime_data(order.pt_symbol)

        if hq is not None:
            now_price = float(hq.loc[0, "price"])
            if order.price_type == PriceType.MARKET.value:
                order.order_price = now_price
                # 订单成交
                self.on_orders_deal(order)
                return

            elif order.price_type == PriceType.LIMIT.value:
                if order.order_type == OrderType.BUY.value:
                    if order.order_price >= now_price:
                        if order.status == Status.SUBMITTING.value:
                            order.trade_price = now_price
                        # 订单成交
                        self.on_orders_deal(order)
                        return
                else:
                    if order.order_price <= now_price:
                        if order.status == Status.SUBMITTING.value:
                            order.trade_price = now_price
                        # 订单成交
                        self.on_orders_deal(order)
                        return

            # 没有成交更新订单状态
            self.on_orders_status_modify(order)

    def on_orders_deal(self, order: Order):
        """订单成交"""
        if not order.trade_price:
            order.trade_price = order.order_price
        order.traded = order.volume
        order.trade_type = self.turnover_mode

        event = Event(EVENT_ORDER_DEAL, order)
        self.event_engine.put(event)

        self.write_log(
            "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                order.account_id,
                order.order_id,
                "全部成交"))

    def on_order_canceled(self, token, order_id):
        """订单取消"""
        data = dict()
        data['token'] = token
        data['order_id'] = order_id
        event = Event(EVENT_ORDER_CANCELED, data)
        self.event_engine.put(event)

    def on_order_rejected(self, order: Order, msg: str = ""):
        """订单被拒绝"""
        order.status = Status.REJECTED.value
        order.error_msg = msg
        event = Event(EVENT_ORDER_REJECTED, order)
        self.event_engine.put(event)

    def on_orders_book_rejected_all(self):
        """拒绝所有订单"""
        if self.orders_book:
            for order in self.orders_book.values():
                order.status = Status.REJECTED.value
                order.error_msg = "交易关闭，自动拒单"

                event = Event(EVENT_ORDER_REJECTED, order)
                self.event_engine.put(event)

                self.write_log(
                    "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                        order.account_id,
                        order.order_id,
                        order.error_msg))

    def on_orders_status_modify(self, order):
        """更新订单状态"""
        raw_data = {}
        raw_data['flt'] = {'order_id': order.order_id}
        raw_data["set"] = {'$set': {'status': Status.NOTTRADED.value}}
        db_data = DBData(
            db_name=SETTINGS['ORDERS_BOOK'],
            db_cl=self.market_name,
            raw_data=raw_data
        )

        return self.db.on_update(db_data)

    def load_orders_today_notrade(self):
        """查询当日未成交的订单"""
        account_list = query_account_list(self.db)

        for account_id in account_list:
            orders = query_orders_today(account_id, self.db)
            if isinstance(orders, list):
                for order in orders:
                    if order['status'] in [Status.NOTTRADED.value, Status.PARTTRADED.value]:
                        order = order_generate(order)
                        self.orders_book[order.order_id] = order

    def on_back_verification(self, order: Order):
        """后端验证"""
        for k, verification in self.verification.items():
            result, msg = verification(order)

            if not result:
                self.on_order_rejected(order, msg)

                self.write_log(
                    "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                        order.account_id, order.order_id, msg))

                return False

        return True

    def time_verification(self):
        """交易时间验证"""
        result = True
        now = datetime.now().time()
        time_dict = {
            "1": (time(9, 15), time(11, 30)),
            "2": (time(13, 0), time(15, 0))
        }
        for k, time_check in time_dict.items():
            if not (now >= time_check[0] and now <= time_check[1]):
                result = False

        if now >= time(15, 1):
            # 市场关闭
            self.on_close()
            result = False

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

    def on_close(self):
        """模拟交易市场关闭"""
        # 阻止接收新订单
        SETTINGS["MARKET_NAME"] = ""

        # 关闭市场撮合
        self._active = False

        # 模拟交易结束，拒绝所有未成交的订单
        self.on_orders_book_rejected_all()

        # 清算
        self.liquidation()

        # 关闭行情接口
        self.hq_client.close()

        # 推送关闭事件
        event = Event(EVENT_MARKET_CLOSE, self.market_name)
        self.event_engine.put(event)

    def liquidation(self):
        """获取收盘数据"""
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

    def write_log(self, msg: str, level: int = INFO):
        """"""
        log = LogData(
            log_content=msg,
            log_level=level
        )
        event = Event(EVENT_LOG, log)
        self.event_engine.put(event)
