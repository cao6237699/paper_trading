
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
from paper_trading.utility.model import Order, Status, LogData
from paper_trading.utility.constant import OrderType, PriceType, TradeType


class Exchange:
    """
    交易所类
    1、其他所有交易市场需要继承此类；
    2、必须重写on_match、on_orders_arrived，verification_register
    """

    def __init__(self, event_engine, account_engine, hq_ser, param):
        self.market_name = ""               # 市场名称
        self._active = False                # 市场状态标识
        self.orders_book = OrderedDict()    # 订单薄用于成交撮合

        # 事件引擎
        self.event_engine = event_engine

        # 账户引擎
        self.account_engine = account_engine

        # 行情源实例
        self.hq_client = hq_ser

        self.exchange_symbols = []          # 交易市场标识
        self.turnover_mode = None           # 回转交易模式
        self.verification = OrderedDict()   # 订单验证清单

    def on_init(self):
        """初始化"""
        # 开启交易撮合开关
        self._active = True

        # 注册验证程序
        self.verification_register()

        # 返回订单接收函数
        return self.on_orders_arrived

    def on_match(self):
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

        self.account_engine.orders_deal(order)

    def on_order_cancel(self, order: Order):
        """订单被取消"""
        self.account_engine.orders_cancel(order)

    def on_order_refused(self, order: Order):
        """订单被拒单"""
        self.account_engine.orders_refused(order)

    def on_order_status_update(self, order: Order):
        """订单状态变化"""
        self.account_engine.orders_status_update(order)

    def load_data(self):
        """加载订单"""
        orders_book = self.account_engine.load_data()
        self.orders_book.update(orders_book)
        self.write_log(f"加载未处理订单共计：{str(len(self.orders_book))}条")

    def on_refused_all(self):
        """拒绝所有订单"""
        if self.orders_book:
            for order in self.orders_book.values():
                order.status = Status.REJECTED.value
                order.error_msg = "交易关闭，自动拒单"
                self.on_order_refused(order)

                self.write_log(
                    "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                        order.account_id,
                        order.order_id,
                        order.error_msg))

        self.orders_book.clear()

    def liquidation(self):
        """收盘清算"""
        self.account_engine.liquidation(self.hq_client)

        self.write_log("{}: 账户与持仓清算完成".format(self.market_name))

    def on_close(self):
        """模拟交易市场关闭"""
        # 关闭市场撮合
        self._active = False

        # 模拟交易结束，拒绝所有未成交的订单
        self.on_refused_all()

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
            if (now >= time_check[0]) and (now <= time_check[1]):
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
                self.on_order_refused(order)
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

    def __init__(self, event_engine, account_engine, hq_ser, param):
        super(BacktestMarket, self).__init__(event_engine, account_engine, hq_ser, param)

        self.market_name = "backtest_market"            # 交易市场名称
        self.turnover_mode = TradeType.T_PLUS1.value    # 交收类型
        self.orders_queue = Queue()                     # 使用订单队列

    def on_match(self):
        """交易撮合"""
        self.write_log("{}：交易市场已开启".format(self.market_name))

        try:
            while self._active:
                if self.orders_queue.empty():
                    continue

                order = self.orders_queue.get(block=True)

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

        # 后端订单验证
        if not self.on_back_verification(order):
            return False

        # 订单推送到订单撮合引擎
        self.orders_queue.put(order)


class ChinaAMarket(Exchange):
    """中国A股交易市场"""

    def __init__(self, event_engine, account_engine, hq_ser, param):
        super(ChinaAMarket, self).__init__(event_engine, account_engine, hq_ser, param)

        self.market_name = "china_a_market"            # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]           # 交易市场标识
        self.turnover_mode = TradeType.T_PLUS1.value   # 回转交易模式

    def on_match(self):
        """交易撮合"""
        self.write_log("{}：交易市场已开启".format(self.market_name))
        try:
            # 行情连接
            self.hq_client.connect_api()

            # 加载数据
            self.load_data()

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
                self.on_order_cancel(order)
                return True
            else:
                return False
        # 过滤掉清算订单
        elif order.order_type == OrderType.LIQ.value:
            return False
        else:
            # 后端订单验证
            if not self.on_back_verification(order):
                return False
            else:
                # 更新订单状态及信息
                order.status = Status.NOTTRADED.value
                self.on_order_status_update(order)
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
