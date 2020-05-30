
import logging

from paper_trading.utility.model import LogData
from paper_trading.utility.constant import Status, LoadDataMode
from paper_trading.event import Event
from paper_trading.utility.event import *
from paper_trading.trade.db_model import *
from paper_trading.trade.account import Trader, order_generate


class AccountEngine():
    """账户引擎"""
    def __init__(
            self,
            event_engine,
            pst_active,
            load_data_mode,
            db,
    ):
        self.event_engine = event_engine        # 事件引擎
        self.db = db                            # 数据库实例
        self.pst_active = pst_active            # 数据持久化开关
        self.load_data_mode = load_data_mode    # 加载数据的模式

        # 交易账户字典
        self.trader_dict = dict()               # 交易账户字典

        # 注册事件监听
        self.event_register()

        self.write_log("账户引擎：初始化完毕")

    def event_register(self):
        """注册事件监听"""
        self.event_engine.register(EVENT_ACCOUNT_UPDATE, self.process_account_update)
        self.event_engine.register(EVENT_ACCOUNT_AVL_UPDATE, self.process_account_avl_update)
        self.event_engine.register(EVENT_ACCOUNT_ASSETS_UPDATE, self.process_account_assets_update)
        self.event_engine.register(EVENT_POS_INSERT, self.process_pos_insert)
        self.event_engine.register(EVENT_POS_UPDATE, self.process_pos_update)
        self.event_engine.register(EVENT_POS_AVL_UPDATE, self.process_pos_avl_update)
        self.event_engine.register(EVENT_POS_PRICE_UPDATE, self.process_pos_price_update)
        self.event_engine.register(EVENT_POS_DELETE, self.process_pos_delete)
        self.event_engine.register(EVENT_ORDER_INSERT, self.process_order_insert)
        self.event_engine.register(EVENT_ORDER_UPDATE, self.process_order_update)
        self.event_engine.register(EVENT_ORDER_STATUS_UPDATE, self.process_order_status_update)
        self.event_engine.register(EVENT_ACCOUNT_RECORD_INSERT, self.process_account_record_insert)
        self.event_engine.register(EVENT_POS_RECORD_INSERT, self.process_pos_record_insert)
        self.event_engine.register(EVENT_POS_RECORD_BUY, self.process_pos_record_buy)
        self.event_engine.register(EVENT_POS_RECORD_SELL, self.process_pos_record_sell)
        self.event_engine.register(EVENT_POS_RECORD_CLEAR, self.process_pos_record_clear)

    def start(self):
        """引擎初始化"""
        self.write_log("账户引擎：启动")

        return self

    def load_data(self):
        """
        加载数据
        用于在系统意外停止后，重启时加载数据使用
        :return:
        """
        account_list = query_account_list(self.db)
        orders_book = dict()
        for account_id in account_list:
            orders = query_orders_today(account_id, self.db)
            if isinstance(orders, list):
                # 加载账户数据
                self.load_trader_data(account_id)

                # 加载订单数据
                for order in orders:
                    order = order_generate(order)
                    if order.status in [Status.SUBMITTING.value,
                                           Status.NOTTRADED.value,
                                           Status.PARTTRADED.value]:
                        # 未成交的订单添加到订单薄
                        orders_book[order.order_id] = order

        return orders_book

    def load_trader_data(self, account_id):
        """加载交易员数据"""
        account = query_account_one(account_id, self.db)

        if isinstance(account, dict):
            trader = Trader(self.event_engine,
                            account,
                            self.pst_active,
                            LoadDataMode.TRADING,
                            self.db)
            self.trader_dict[account_id] = trader

    def creat(self, info: dict):
        """创建账户"""
        account_dict = on_account_add(info, self.db)
        if account_dict:
            token = account_dict['account_id']
            if not self.trader_dict.get(token):
                account = Trader(self.event_engine,
                                 account_dict,
                                 self.pst_active,
                                 LoadDataMode.CREAT,
                                 self.db)
                self.trader_dict[token] = account
                return account_dict

    def login(self, token: str):
        """
        账户登录
        账户登录的过程就是将账户信息、持仓信息、订单信息加载到内存中，
        并将账户所有信息比拟一个交易员放到交易员字典中
        :param token: 账户ID
        :param db: 数据库对象
        :return: None
        """
        trader = self.trader_dict.get(token)
        # 账户未登陆
        if not trader:
            # 查询账户
            account_dict = query_account_one(token, self.db)
            if account_dict:
                account = Trader(self.event_engine,
                                 account_dict,
                                 self.pst_active,
                                 self.load_data_mode,
                                 self.db)
                self.trader_dict[token] = account
                return account_dict
            else:
                return False
        else:
            account = copy.deepcopy(trader.account)
            return account.__dict__

    def logout(self, token: str):
        """账户登出"""
        if self.trader_dict.get(token, None):
            del self.trader_dict[token]

    def orders_arrived(self, order: Order):
        """订单到达处理"""
        trader = self.trader_dict.get(order.account_id)
        if trader:
            status, msg = trader.on_orders_arrived(order)
            return status, msg
        else:
            return False, "交易账户未登陆"

    def orders_deal(self, order: Order):
        """订单成交处理"""
        trader = self.trader_dict.get(order.account_id)
        trader.on_order_deal(order)

    def orders_cancel(self, order: Order):
        """订单成交处理"""
        trader = self.trader_dict.get(order.account_id)
        trader.on_order_cancel(order)

    def orders_refused(self, order: Order):
        """订单成交处理"""
        trader = self.trader_dict.get(order.account_id)
        trader.on_order_refuse(order)

    def orders_status_update(self, order: Order):
        """订单成交处理"""
        trader = self.trader_dict.get(order.account_id)
        trader.on_order_status_update(order)

    def liquidation(self, hq_client):
        """清算"""
        today = datetime.now().strftime("%Y%m%d")

        for token, trader in self.trader_dict.items():
            for symbol, pos in trader.pos.items():
                hq = hq_client.get_realtime_data(symbol)
                if hq is not None:
                    now_price = float(hq.loc[0, "price"])
                    # 更新收盘行情
                    trader.on_position_update_price(pos, now_price)
            # 清算
            trader.on_liquidation(today)

    def liq_manual(self, token, liq_date, price_dict):
        """手工清算"""
        trader = self.trader_dict.get(token)

        if trader:
            if trader.on_liquidation(liq_date, price_dict):
                return True
        # 账户未登陆
        else:
            return False

    def query_account_data(self, token: str):
        """
        查询账户信息
        如果引擎工作正常则从内存中找到账户的最新数据，如果没有则从数据库中找数据
        :param token: 账户ID
        :return: 账户数据字典
        """
        trader = self.trader_dict.get(token, None)
        if trader:
            account = trader.account
            return True, account.__dict__
        else:
            return False, "账户未登录"

    def query_pos_data(self, token: str):
        """
        查询持仓信息
        如果引擎工作正常则从内存中找到持仓的最新数据，如果没有则从数据库中找数据
        :param token: 账户ID
        :return: 持仓数据列表
        """
        trader = self.trader_dict.get(token, None)
        if trader:
            pos = copy.copy(trader.pos)
            if pos:
                pos_data = [d.__dict__ for d in pos.values()]
                return True, pos_data
            else:
                return True, []
        else:
            return False, "账户未登录"

    def query_orders_today(self, token: str):
        """查询当天交易订单"""
        trader = self.trader_dict.get(token, None)
        if trader:
            orders = list()
            for d in trader.orders.values():
                orders.append(d.__dict__)

            if orders:
                return True, orders
            else:
                return True, "无委托记录"
        else:
            return False, "账户未登录"

    def query_orders(self, token: str):
        """查询所有订单"""
        # 检查账户登录情况
        trader = self.trader_dict.get(token, None)
        if trader:
            orders = list()
            for d in trader.orders.values():
                orders.append(d.__dict__)

            if orders:
                return True, orders
            else:
                return True, "无委托记录"
        else:
            return False, "账户未登录"

    def query_account_record(self, token: str, start=None, end=None):
        """查询账户记录"""
        trader = self.trader_dict.get(token, None)
        if trader:
            records = list()
            df = trader.account_record
            if len(df):
                if start and end:
                    df = df.loc[(df['check_date'] >= start) & (df['check_date'] <= end)]
                elif start and not end:
                    df = df.loc[(df['check_date'] >= start)]
                elif not start and end:
                    df = df.loc[(df['check_date'] <= end)]
                elif not start and not end:
                    pass
                records = df.to_dict(orient='records')

            if records:
                return True, records
            else:
                return False, "无账户记录"
        else:
            return True, "账户未登录"

    def query_pos_record(self, token: str, start=None, end=None):
        """查询持仓记录"""
        trader = self.trader_dict.get(token, None)
        if trader:
            records = list()
            df = trader.pos_record
            if len(df):
                if start and end:
                    df = df.loc[(df['first_buy_date'] >= start) & (df['last_sell_date'] <= end)]
                elif start and not end:
                    df = df.loc[(df['first_buy_date'] >= start)]
                elif not start and end:
                    df = df.loc[(df['last_sell_date'] <= end)]
                elif not start and not end:
                    pass
                records = df.to_dict(orient='records')

            if records:
                return True, records
            else:
                return True, "无持仓记录"
        else:
            return False, "账户未登录"

    def data_persistance(self, token: str):
        """持久化数据"""
        trader = self.trader_dict.get(token)
        if trader:
            # 持久化账户数据
            account = trader.account
            on_account_update({
                'token': account.account_id,
                'avl': account.available,
                'market_value': account.market_value,
                'assets': account.assets
            }, self.db)

            # 持久化持仓数据
            on_position_clear(token, self.db)
            for symbol, pos in trader.pos.items():
                pos_copy = copy.copy(pos)
                on_position_insert(pos_copy, self.db)


            # 持久化订单数据
            on_orders_clear(token, self.db)
            orders_copy = copy.deepcopy(trader.orders)
            orders = [order.__dict__ for order in orders_copy.values()]
            on_orders_insert_many(token, orders, self.db)

            # 持久化账户记录数据
            account_record_clear(token, self.db)
            account_record_list = trader.account_record.to_dict(orient='records')
            account_record_insert_many(token, account_record_list, self.db)

            # 持久化持仓记录数据
            pos_record_clear(token, self.db)
            pos_record_list = trader.pos_record.to_dict(orient='records')
            pos_record_insert_many(token, pos_record_list, self.db)

            return True
        else:
            return "账户未登录"

    def process_order_insert(self, event):
        """处理订单插入事件"""
        order = event.data
        on_orders_insert(order, self.db)

    def process_account_update(self, event):
        """处理账户更新事件"""
        data = event.data
        on_account_update(data, self.db)

    def process_account_avl_update(self, event):
        """处理账户可用资金更新"""
        data = event.data
        on_account_avl_update(data, self.db)

    def process_account_assets_update(self, event):
        """处理账户资产更新"""
        data = event.data
        on_account_assets_update(data, self.db)

    def process_pos_insert(self, event):
        """处理持仓新增事件"""
        pos = event.data
        on_position_insert(pos, self.db)

    def process_pos_update(self, event):
        """处理持仓更新事件"""
        pos = event.data
        on_position_update(pos, self.db)

    def process_pos_avl_update(self, event):
        """处理可用股份更新"""
        data = event.data
        on_position_avl_update(data, self.db)

    def process_pos_price_update(self, event):
        """处理可用股份更新"""
        data = event.data
        on_position_price_update(data, self.db)

    def process_pos_delete(self, event):
        """处理可用股份更新"""
        data = event.data
        on_position_delete(data, self.db)

    def process_order_update(self, event):
        """处理订单更新事件"""
        data = event.data
        on_order_update(data, self.db)

    def process_order_status_update(self, event):
        """处理订单更新事件"""
        data = event.data
        on_order_status_update(data, self.db)

    def process_account_record_insert(self, event):
        """处理账户记录创建事件"""
        account_daily = event.data
        account_record_creat(account_daily, self.db)

    def process_pos_record_insert(self, event):
        """处理持仓记录事件"""
        pos_record = event.data
        pos_record_creat(pos_record, self.db)

    def process_pos_record_buy(self, event):
        """处理持仓记录事件"""
        data = event.data
        pos_record_update_buy(data, self.db)

    def process_pos_record_sell(self, event):
        """处理持仓记录事件"""
        data = event.data
        pos_record_update_sell(data, self.db)

    def process_pos_record_clear(self, event):
        """处理持仓记录事件"""
        data = event.data
        pos_record_update_liq(data, self.db)

    def write_log(self, msg: str, level: int = logging.INFO):
        """"""
        log = LogData(
            log_content=msg,
            log_level=level
        )
        event = Event(EVENT_LOG, log)
        self.event_engine.put(event)