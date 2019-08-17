
from time import sleep
from logging import INFO
from datetime import datetime, time
from collections import OrderedDict

from paper_trading.event import Event
from paper_trading.utility.event import (
    EVENT_ERROR,
    EVENT_LOG,
    EVENT_MARKET_CLOSE,
    EVENT_ORDER_DEAL,
    EVENT_ORDER_REJECTED
)
from paper_trading.utility.setting import SETTINGS
from paper_trading.api.tushare_api import TushareService
from paper_trading.trade.account import (
    order_generate,
    query_account_list,
    query_position,
    on_position_update_price,
    on_liquidation
)
from paper_trading.utility.model import Order, DBData, Status, LogData
from paper_trading.utility.constant import OrderType, PriceType, TradeType, EngineMode


class Exchange(object):
    """交易所"""

    def __init__(self, event_engine):
        self.market_name = ""              # 市场名称
        self._active = False
        self.event_engine = event_engine   # 事件引擎
        self.hq_client = None              # 行情源
        self.match_mode = None             # 模拟交易引擎类型
        self.period = SETTINGS["PERIOD"]   # 撮合效率，单位秒
        self.exchange_symbols = []         # 交易市场标识
        self.turnover_mode = None          # 回转交易模式

    def on_match(self, db):
        """"""
        pass

    def on_realtime_match(self, db):
        """实时交易撮合"""
        pass

    def on_simulation_match(self, db):
        """模拟交易撮合"""
        pass

    def query_orders_book(self, db):
        """查询订单薄中的订单"""
        pass

    def on_close(self, db):
        """市场关闭"""
        pass

    def on_liquidation(self, db):
        """清算"""


class ChinaAMarket(Exchange):
    """中国A股交易市场"""

    def __init__(self, event_engine):
        super(ChinaAMarket, self).__init__(event_engine)

        self.market_name = "china_a_market"            # 交易市场名称
        self._active = False
        self.hq_client = TushareService()              # 行情源
        self.exchange_symbols = ["SH", "SZ"]           # 交易市场标识
        self.match_mode = SETTINGS["ENGINE_MODE"]      # 模拟交易引擎类型
        self.turnover_mode = TradeType.T_PLUS1.value   # 回转交易模式
        self.verification = OrderedDict()              # 验证清单

        self.on_init()

    def on_init(self):
        """初始化"""
        # 绑定交易市场名称，用于订单薄接收订单
        SETTINGS["MARKET_NAME"] = self.market_name

        # 注册验证程序
        if self.match_mode == EngineMode.REALTIME.value:
            self.verification = {
                "1": self.product_verification,
                "2": self.price_verification,
            }
        else:
            self.verification = {
                "1": self.product_verification,
            }

        # 开启交易撮合循环
        self._active = True

    def on_match(self, db):
        """交易撮合"""
        self.write_log("{}：交易市场已开启".format(self.market_name))

        try:
            if self.match_mode == EngineMode.REALTIME.value:
                self.on_realtime_match(db)
            else:
                self.on_simulation_match(db)

        except Exception as e:
            event = Event(EVENT_ERROR, e)
            self.event_engine.put(event)

    def on_realtime_match(self, db):
        """实时交易撮合"""
        self.write_log("{}：真实行情".format(self.market_name))

        # 行情连接
        self.hq_client.connect_api()

        while self._active:
            sleep(3)
            # 交易时间检验
            if not self.time_verification(db):
                continue

            # 获取最新的订单
            orders = self.query_orders_book(db)

            if not orders:
                continue

            for order in orders:
                order = order_generate(order)
                # 订单验证
                if not self.on_back_verification(order):
                    self.on_orders_book_delete(order, db)
                else:
                    # 订单撮合
                    self.on_orders_match(order, db)

    def on_simulation_match(self, db):
        """模拟交易撮合"""
        self.write_log("{}：模拟行情".format(self.market_name))

        while self._active:
            # 获取最新的订单
            orders = self.query_orders_book(db)

            if not orders:
                continue

            for order in orders:
                order = order_generate(order)

                # 订单验证
                if not self.on_back_verification(order):
                    self.on_orders_book_delete(order, db)
                    continue

                # 订单成交
                self.on_orders_deal(order, db)

    def on_orders_match(self, order: Order, db):
        """订单撮合"""
        hq = self.hq_client.get_realtime_data(order.pt_symbol)

        if hq is not None:
            now_price = float(hq.loc[0, "price"])
            if order.price_type == PriceType.MARKET.value:
                order.order_price = now_price
                # 订单成交
                self.on_orders_deal(order, db)
                return

            elif order.price_type == PriceType.LIMIT.value:
                if order.order_type == OrderType.BUY.value:
                    if order.order_price >= now_price:
                        if order.status == Status.SUBMITTING.value:
                            order.trade_price = now_price
                        # 订单成交
                        self.on_orders_deal(order, db)
                        return
                else:
                    if order.order_price <= now_price:
                        if order.status == Status.SUBMITTING.value:
                            order.trade_price = now_price
                        # 订单成交
                        self.on_orders_deal(order, db)
                        return

            # 没有成交更新订单状态
            self.on_orders_status_modify(order, db)

    def on_orders_deal(self, order: Order, db):
        """订单成交"""
        if not order.trade_price:
            order.trade_price = order.order_price
        order.traded = order.volume
        order.trade_type = self.turnover_mode

        self.on_orders_book_delete(order, db)

        event = Event(EVENT_ORDER_DEAL, order)
        self.event_engine.put(event)

        self.write_log(
            "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                order.account_id,
                order.order_id,
                "全部成交"))

    def on_orders_book_update(self, order: Order, db):
        """订单薄更新订单"""
        raw_data = {}
        raw_data['flt'] = {'order_id': order.order_id}
        raw_data["set"] = {'$set': {'volume': (order.volume - order.traded),
                                    'traded': 0}}
        db_data = DBData(
            db_name=SETTINGS['ORDERS_BOOK'],
            db_cl=self.market_name,
            raw_data=raw_data
        )

        return db.on_update(db_data)

    def on_orders_book_delete(self, order: Order, db):
        """订单薄删除订单"""
        raw_data = {}
        raw_data['flt'] = {'order_id': order.order_id}
        db_data = DBData(
            db_name=SETTINGS['ORDERS_BOOK'],
            db_cl=self.market_name,
            raw_data=raw_data
        )

        db.on_delete(db_data)

    def on_orders_book_rejected_all(self, db):
        """拒绝所有订单"""
        orders = self.query_orders_book(db)

        if orders:
            for order in orders:
                order = order_generate(order)
                self.on_orders_book_delete(order, db)

                order.status = Status.REJECTED.value
                order.error_msg = "交易关闭，自动拒单"

                event = Event(EVENT_ORDER_REJECTED, order)
                self.event_engine.put(event)

                self.write_log(
                    "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                        order.account_id,
                        order.order_id,
                        order.error_msg))

    def on_orders_status_modify(self, order, db):
        """更新订单状态"""
        raw_data = {}
        raw_data['flt'] = {'order_id': order.order_id}
        raw_data["set"] = {'$set': {'status': Status.NOTTRADED.value}}
        db_data = DBData(
            db_name=SETTINGS['ORDERS_BOOK'],
            db_cl=self.market_name,
            raw_data=raw_data
        )

        return db.on_update(db_data)

    def query_orders_book(self, db, token: str = ""):
        """查询订单薄中的订单"""
        raw_data = {}
        raw_data["flt"] = {"account_id": token}
        if not token:
            raw_data["flt"] = {}

        db_data = DBData(
            db_name=SETTINGS['ORDERS_BOOK'],
            db_cl=self.market_name,
            raw_data=raw_data
        )
        return db.on_select(db_data)

    def on_back_verification(self, order: Order):
        """后端验证"""
        for k, verification in self.verification.items():
            result, msg = verification(order)

            if not result:
                order.status = Status.REJECTED.value
                order.error_msg = msg

                event = Event(EVENT_ORDER_REJECTED, order)
                self.event_engine.put(event)

                self.write_log(
                    "处理订单：账户：{}, 订单号：{}, 结果：{}".format(
                        order.account_id, order.order_id, msg))

                return False

        return True

    def time_verification(self, db):
        """交易时间验证"""
        result = True
        now = datetime.now().time()
        time_dict = {
            "1": (time(9, 15), time(11, 30)),
            "2": (time(13, 0), time(15, 0))
        }
        for k, time_check in time_dict.items():
            if (now >= time_check[0] and now <= time_check[1]):
                result = True
            else:
                if now >= time(15, 1):
                    # 市场关闭
                    self.on_close(db)
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

    def on_close(self, db):
        """模拟交易市场关闭"""
        # 阻止接收新订单
        SETTINGS["MARKET_NAME"] = ""

        # 关闭市场撮合
        self._active = False

        # 模拟交易结束，拒绝所有未成交的订单
        self.on_orders_book_rejected_all(db)

        # 清算
        self.on_liquidation(db)

        # 关闭行情接口
        self.hq_client.close()

        # 推送关闭事件
        event = Event(EVENT_MARKET_CLOSE, self.market_name)
        self.event_engine.put(event)

    def on_liquidation(self, db):
        """获取收盘数据"""
        tokens = query_account_list(db)

        if tokens:
            for token in tokens:
                pos_list = query_position(token, db)
                if isinstance(pos_list, list):
                    for pos in pos_list:
                        hq = self.hq_client.get_realtime_data(pos["pt_symbol"])
                        if hq is not None:
                            now_price = float(hq.loc[0, "price"])
                            # 更新收盘行情
                            on_position_update_price(token, pos, now_price, db)
                # 清算
                on_liquidation(db, token)
        self.write_log("{}: 账户与持仓清算完成".format(self.market_name))

    def write_log(self, msg: str, level: int = INFO):
        """"""
        log = LogData(
            log_content=msg,
            log_level=level
        )
        event = Event(EVENT_LOG, log)
        self.event_engine.put(event)
