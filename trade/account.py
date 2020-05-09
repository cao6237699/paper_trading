
import copy
import time
import pandas as pd

from paper_trading.event import Event
from paper_trading.utility.event import *
from paper_trading.utility.setting import SETTINGS
from paper_trading.trade.db_model import (
    query_position,
    query_orders,
    query_orders_today,
    query_account_record,
    query_pos_records,
    query_pos_records_not_clear
)
from paper_trading.utility.constant import (
    Status,
    OrderType,
    TradeType,
    PriceType,
    LoadDataMode
)
from paper_trading.utility.model import (
    Account,
    AccountRecord,
    Position,
    PosRecord,
    Order
)


# 小数点保留位数
P = SETTINGS["POINT"]


class Trader:
    """交易员"""

    def __init__(self,
                 event_engine,
                 account_dict: dict,
                 pst_active,
                 load_data_mode,
                 db):
        """构造函数"""
        self.event_engine = event_engine            # 事件引擎
        self.__pst_active = pst_active              # 数据持久化开关
        account = account_generate(account_dict)
        self.token = account.account_id
        self.account = account

        self.pos = dict()                           # 持仓数据
        self.orders = dict()                        # 订单数据
        self.orders_today = dict()                  # 今日订单数据
        self.account_record = pd.DataFrame()        # 账户记录
        self.pos_record = pd.DataFrame()            # 持仓记录

        # 加载数据
        self.__load_data(load_data_mode, db)

    def __load_data(self, load_data_mode, db):
        """加载数据"""
        # 新建模式：不用加载数据
        if load_data_mode == LoadDataMode.CREAT:
            pass
        # 回测模式：加载所有数据
        elif load_data_mode == LoadDataMode.BACKTEST:
            self.__load_pos(db)
            self.__load_orders(db)
            self.__load_account_records(db)
            self.__load_pos_records(db)
        # 交易模式：加载当前持仓，当日的订单及未清仓的持仓记录
        elif load_data_mode == LoadDataMode.TRADING:
            self.__load_pos(db)
            self.__load_orders(db)
            self.__load_today_orders(db)
            self.__load_pos_records_not_clear(db)
        else:
            raise ValueError("数据加载模式错误")

    def __load_pos(self, db):
        """加载持仓"""
        data = query_position(self.token, db)
        if isinstance(data, list):
            for d in data:
                pos = pos_generate(d)
                self.pos[pos.pt_symbol] = pos

    def __load_orders(self, db):
        """加载所有订单数据"""
        data = query_orders(self.token, db)
        if isinstance(data, list):
            for d in data:
                order = order_generate(d)
                self.orders[order.order_id] = order

    def __load_today_orders(self, db):
        """加载当日订单"""
        data = query_orders_today(self.token, db)
        if isinstance(data, list):
            for d in data:
                order = order_generate(d)
                self.orders_today[order.order_id] = order

    def __load_account_records(self, db):
        """加载账户记录"""
        account_record = query_account_record(self.token, db)
        if account_record:
            self.account_record = pd.DataFrame(account_record, index=[i for i in range(len(account_record))])

    def __load_pos_records(self, db):
        """加载所有持仓记录"""
        pos_record = query_pos_records(self.token, db)
        if pos_record:
             self.pos_record = pd.DataFrame(pos_record, index=[i for i in range(len(pos_record))])

    def __load_pos_records_not_clear(self, db):
        """加载未清仓的持仓记录数据"""
        pos_record = query_pos_records_not_clear(self.token, db)
        if pos_record:
             self.pos_record = pd.DataFrame(pos_record, index=[i for i in range(len(pos_record))])

    def __make_event(self, event_name, data):
        """制造事件"""
        if self.__pst_active:
            new_data = copy.deepcopy(data)
            event = Event(event_name, new_data)
            self.event_engine.put(event)

    def on_orders_arrived(self, order: Order):
        """订单到达"""
        # 接收订单前的验证
        if SETTINGS['VERIFICATION']:
            result, msg = self.__on_front_verification(order)
            if not result:
                return result, msg

        # 生成订单ID
        order.order_id = str(time.time())

        # 补充订单信息
        if order.order_price == 0:
            order.price_type = PriceType.MARKET.value
        else:
            order.price_type = PriceType.LIMIT.value

        self.orders[order.order_id] = order

        # 推送订单保存事件
        self.__make_event(EVENT_ORDER_INSERT, order)

        return True, order

    def on_order_deal(self, order: Order):
        """订单成交处理"""
        # 买入处理
        if order.order_type == OrderType.BUY.value:
            pos_val_diff = self.__on_position_append(order)
            self.__on_account_buy(order, pos_val_diff)
        # 卖出处理
        else:
            pos_val_diff = self.__on_position_reduce(order)
            self.__on_account_sell(order, pos_val_diff)

        if order.volume == order.traded:
            order.status = Status.ALLTRADED.value
        else:
            order.status = Status.PARTTRADED.value

        # 订单更新
        new_order = copy.copy(order)
        self.orders[order.order_id] = new_order

        # 订单更新事件
        self.__make_event(EVENT_ORDER_UPDATE, order)

    def on_order_cancel(self, order: Order):
        """取消订单"""
        order.status = Status.CANCELLED.value
        self.on_order_refuse(order)

    def on_order_refuse(self, order: Order):
        """拒绝订单"""
        # 更新订单
        self.orders[order.order_id].status = order.status
        self.orders[order.order_id].error_msg = order.error_msg

        # 推送订单状态修改事件
        self.__make_event(EVENT_ORDER_STATUS_UPDATE, {
            'token': order.account_id,
            'id': order.order_id,
            'status': order.status,
            'msg': order.error_msg
        })

        if order.order_type == OrderType.BUY.value:
            return self.__on_buy_cancel(order)
        else:
            return self.__on_sell_cancel(order)

    def on_order_status_update(self, order: Order):
        """更新订单状态信息"""
        self.orders[order.order_id].status = order.status

        # 推送订单状态修改事件
        self.__make_event(EVENT_ORDER_STATUS_UPDATE, {
            'token': order.account_id,
            'id': order.order_id,
            'status': order.status,
            'msg': order.error_msg
        })

    def __on_account_buy(self, order: Order, pos_val_diff):
        """买入成交后账户操作"""
        old_pos_val = self.account.market_value
        market_value = round((old_pos_val + pos_val_diff), P)
        frozen_all = self.account.assets - \
                     self.account.available - old_pos_val
        frozen = (order.volume * order.order_price) * (1 + self.account.cost)
        pay = (order.traded * order.trade_price) * (1 + self.account.cost)

        available = round((self.account.available + frozen - pay), P)
        frozen_all = frozen_all - frozen
        assets = round((available + market_value + frozen_all), P)

        # 更新账户信息
        self.account.market_value = market_value
        self.account.available = available
        self.account.assets = assets

        # 推送账户更新事件
        self.__make_event(EVENT_ACCOUNT_UPDATE, {
            'token': self.token,
            'avl': available,
            'market_value': market_value,
            'assets': assets
        })

    def __on_account_sell(self, order: Order, pos_val_diff):
        """卖出成交后账户操作"""
        old_pos_val = self.account.market_value
        market_value = round((old_pos_val + pos_val_diff), P)
        frozen = self.account.assets - self.account.available - old_pos_val
        order_val = order.traded * order.trade_price
        cost = order_val * self.account.cost
        tax = order_val * self.account.tax
        available = round((self.account.available + order_val - cost - tax), P)
        assets = round((available + market_value + frozen), P)

        # 更新账户信息
        self.account.market_value = market_value
        self.account.available = available
        self.account.assets = assets

        # 推送账户更新事件
        self.__make_event(EVENT_ACCOUNT_UPDATE, {
            'token': self.token,
            'avl': available,
            'market_value': market_value,
            'assets': assets
        })

    def __on_account_assets_update(self, value: float):
        """账户资产更新"""
        assets = self.account.assets + value
        market_value = self.account.market_value + value
        # 更新账户市值
        self.account.assets = assets
        self.account.market_value = market_value

        # 推送账户市值变更事件
        self.__make_event(EVENT_ACCOUNT_ASSETS_UPDATE, {
            'token': self.token,
            'market_value': market_value,
            'assets': assets
        })

    def __on_position_insert(self, order: Order, cost: float):
        """持仓增加"""
        profit = round((cost * -1), P)
        available = order.traded
        if order.trade_type == TradeType.T_PLUS1.value:
            available = 0

        pos = Position(
            code=order.code,
            exchange=order.exchange,
            account_id=order.account_id,
            buy_date=order.order_date,
            volume=order.traded,
            available=available,
            buy_price=order.trade_price,
            now_price=order.trade_price,
            profit=profit
        )

        self.pos[order.pt_symbol] = copy.copy(pos)
        pos_val = pos.volume * pos.now_price

        # 推送持仓新建事件
        self.__make_event(EVENT_POS_INSERT, pos)

        # 创建持仓记录
        pos_record = PosRecord(
            code=pos.code,
            exchange=pos.exchange,
            account_id=pos.account_id,
            first_buy_date=pos.buy_date,
            last_sell_date="",
            max_vol=pos.volume,
            buy_price_mean=pos.buy_price,
            sell_price_mean=0.0,
            profit=pos.profit
        )
        df = pd.DataFrame(pos_record.__dict__, index=[len(self.pos_record)])
        self.pos_record = self.pos_record.append(df)

        # 推送持仓记录新建事件
        self.__make_event(EVENT_POS_RECORD_INSERT, pos_record)

        return pos_val

    def __on_position_append(self, order: Order):
        """持仓增长"""
        cost = order.volume * order.trade_price * self.account.cost

        # 有标的持仓
        old_pos = self.pos.get(order.pt_symbol, None)
        if old_pos:
            old_pos_val = old_pos.volume * old_pos.now_price
            volume = old_pos.volume + order.traded
            now_price = order.trade_price
            profit = round(((order.trade_price -
                      old_pos.now_price) * old_pos.volume + old_pos.profit - cost), P)
            available = old_pos.available + order.traded

            if order.trade_type == TradeType.T_PLUS1.value:
                available = old_pos.available

            buy_price = round((((old_pos.volume * old_pos.buy_price) +
                               (order.traded * order.trade_price)) / volume), P)

            # 更新持仓信息
            new_pos = copy.copy(old_pos)
            new_pos.volume = volume
            new_pos.now_price = now_price
            new_pos.buy_price = buy_price
            new_pos.available = available
            new_pos.profit = profit
            self.pos[order.pt_symbol] = new_pos
            new_pos_val = volume * now_price
            pos_val_diff = new_pos_val - old_pos_val

            # 推送持仓更新事件
            self.__make_event(EVENT_POS_UPDATE, new_pos)

            # 持仓记录更新
            index = self.pos_record.loc[(self.pos_record['pt_symbol']==order.pt_symbol) & (self.pos_record['is_clear']==0)].index.tolist()
            if index:
                i = index[0]
                self.pos_record.loc[i, 'max_vol'] = volume
                self.pos_record.loc[i, 'buy_price_mean'] = buy_price
                self.pos_record.loc[i, 'profit'] = profit

                # 推送持仓增加记录事件
                pos_info = {
                    'token': order.account_id,
                    'symbol': order.pt_symbol,
                    "max_vol": volume,
                    "buy_price_mean": buy_price,
                    "profit": profit
                }
                self.__make_event(EVENT_POS_RECORD_BUY, pos_info)

            return pos_val_diff
        else:
            pos_val_diff = self.__on_position_insert(order, cost)
            return pos_val_diff

    def __on_position_reduce(self, order: Order):
        """持仓减少"""
        old_pos = self.pos.get(order.pt_symbol)

        old_pos_val = old_pos.volume * old_pos.now_price

        volume = old_pos.volume - order.volume
        now_price = order.trade_price
        cost = order.volume * order.trade_price * self.account.cost
        tax = order.volume * order.trade_price * self.account.tax
        profit = round(((order.trade_price - old_pos.now_price) *
                 old_pos.volume + old_pos.profit - cost - tax), P)

        # 更新
        new_pos = copy.copy(old_pos)
        new_pos.volume = volume
        new_pos.now_price = now_price
        new_pos.profit = profit
        self.pos[order.pt_symbol] = new_pos
        new_pos_val = volume * now_price
        pos_val_diff = new_pos_val - old_pos_val

        # 推送持仓更新事件
        self.__make_event(EVENT_POS_UPDATE, new_pos)

        # 持仓记录更新
        index = self.pos_record.loc[(self.pos_record['pt_symbol'] == order.pt_symbol) & (self.pos_record['is_clear'] == 0)].index.tolist()
        if index:
            i = index[0]
            max_vol = int(self.pos_record.loc[i, 'max_vol'])
            sell_price_mean = float(self.pos_record.loc[i, 'sell_price_mean'])
            new_sell_price_mean = sell_price_mean + ((order.volume / max_vol) * now_price)
            self.pos_record.loc[i, 'sell_price_mean'] = new_sell_price_mean
            self.pos_record.loc[i, 'last_sell_date'] = order.order_date
            self.pos_record.loc[i, 'profit'] = profit

            # 推送持仓记录更新
            pos_info = {
                'token': order.account_id,
                'symbol': order.pt_symbol,
                "sell_price_mean": new_sell_price_mean,
                "profit": profit,
                "date": order.order_date
            }
            self.__make_event(EVENT_POS_RECORD_SELL, pos_info)

        return pos_val_diff

    def on_position_update_price(self, pos, price: float):
        """更新持仓价格"""
        volume = pos.volume
        if volume:
            old_value = pos.volume * pos.now_price
            new_value = pos.volume * price
            value_diff = new_value - old_value

            profit = round((price - pos.now_price) * \
                     volume + pos.profit, P)

            # 更新持仓价格
            pos.now_price = price
            pos.profit = profit
            self.pos[pos.pt_symbol] = pos

            # 推送持仓价格更新事件
            self.__make_event(EVENT_POS_PRICE_UPDATE, {
                "token": self.token,
                "symbol": pos.pt_symbol,
                "price": price,
                "profit": profit,
            })

            # 更新账户信息
            self.__on_account_assets_update(value_diff)

    def __on_position_frozen_cancel(self, symbol):
        """持仓解除冻结"""
        volume = self.pos[symbol].volume
        if volume:
            # 更新
            self.pos[symbol].available = volume

            # 推送股份解冻事件
            self.__make_event(EVENT_POS_AVL_UPDATE, {
                "token": self.token,
                "symbol": symbol,
                "avl": volume
            })
        else:
            # 持仓为空的删除持仓信息
            del self.pos[symbol]

            # 推送持仓清空事件
            self.__make_event(EVENT_POS_DELETE, {
                'token': self.token,
                'symbol': symbol
            })

            # 持仓记录更新
            index = self.pos_record.loc[(self.pos_record['pt_symbol'] == symbol) & (self.pos_record['is_clear'] == 0)].index.tolist()
            if index:
                self.pos_record.loc[index[0], 'is_clear'] = 1

            # 推送持仓增加记录事件
            pos_info = {
                'token': self.token,
                'symbol': symbol
            }
            self.__make_event(EVENT_POS_RECORD_CLEAR, pos_info)


    """验证"""

    def __on_front_verification(self, order: Order):
        """订单前置验证"""
        # 对订单的准确性验证
        # TODO

        if order.order_type == OrderType.BUY.value:
            return self.__account_verification(order)
        else:
            return self.__position_verification(order)

    def __account_verification(self, order: Order):
        """订单账户资金验证"""
        # 查询账户信息
        money_need = order.volume * order.order_price * (1 + self.account.cost)

        if self.account.available >= money_need:
            # 资金冻结
            avl_diff = self.account.available - money_need
            self.account.available = avl_diff

            # 推送账户资金冻结事件
            self.__make_event(EVENT_ACCOUNT_AVL_UPDATE, {
                'token':self.token,
                'avl': avl_diff
            })

            return True, ""
        else:
            return False, "账户资金不足"

    def __position_verification(self, order: Order):
        """订单持仓验证"""
        pos_need = order.volume
        pos = self.pos.get(order.pt_symbol, None)
        if pos:
            if pos.available >= pos_need:
                # 更新
                avl_diff = pos.available - pos_need
                self.pos[order.pt_symbol].available = avl_diff

                # 推送股份冻结事件
                self.__make_event(EVENT_POS_AVL_UPDATE, {
                    "token": pos.account_id,
                    "symbol": pos.pt_symbol,
                    "avl": avl_diff
                })

                return True, ""
            else:
                return False, "可用持仓不足"
        else:
            return False, "无可用持仓"

    def __on_buy_cancel(self, order: Order):
        """买入订单取消"""
        pay = (order.volume - order.traded) * \
              order.order_price * (1 + self.account.cost)

        available = self.account.available + pay

        # 更新可用资金
        self.account.available = available

        # 推送资金解冻事件
        self.__make_event(EVENT_ACCOUNT_AVL_UPDATE, {
            'token': self.token,
            'avl': available
        })

    def __on_sell_cancel(self, order: Order):
        """卖出取消"""
        pos = self.pos.get(order.pt_symbol)
        available = pos.available + order.volume - order.traded

        # 股份解冻
        self.pos[order.pt_symbol].available = available

        # 推送股份解冻事件
        self.__make_event(EVENT_POS_AVL_UPDATE, {
            "token": pos.account_id,
            "symbol": pos.pt_symbol,
            "avl": available
        })

    """清算"""

    def on_liquidation(self, liq_date: str, price_dict: dict = None):
        """清算"""
        # 更新所有持仓最新价格并冻结证券，并更新市值
        self.__on_position_liquidation(price_dict)

        # 冻结资金
        self.__on_account_liquidation()

        # 创建账户记录
        account_daily = AccountRecord(
            account_id=self.token,
            check_date=liq_date,
            assets=self.account.assets,
            available=self.account.available,
            market_value=self.account.market_value
        )
        df = pd.DataFrame(account_daily.__dict__, index=[liq_date])
        self.account_record = self.account_record.append(df)

        # 推送账户记录创建事件
        self.__make_event(EVENT_ACCOUNT_RECORD_INSERT, account_daily)

        return True

    def __on_account_liquidation(self):
        """账户清算"""
        # 解除冻结
        available = self.account.assets - self.account.market_value

        # 更新账户可用资金
        self.account.available = available

        # 推送资金解冻事件
        self.__make_event(EVENT_ACCOUNT_AVL_UPDATE, {
            'token': self.token,
            'avl': available
        })

    def __on_position_liquidation(self, price_dict: dict = None):
        """持仓清算"""
        for symbol in list(self.pos.keys()):
            if price_dict:
                pos = self.pos.get(symbol)
                if pos.pt_symbol in price_dict.keys():
                    # 更新最新价格并解除账户冻结
                    new_price = price_dict.get(pos.pt_symbol)
                    self.on_position_update_price(pos, new_price)

            # 解除账户冻结
            self.__on_position_frozen_cancel(symbol)


"""数据对象生成器"""


def account_generate(d: dict):
    """订单生成器"""
    account = Account(
        account_id=d['account_id'],
        assets=round(d['assets'], P),
        available=round(d['available'], P),
        market_value=round(d['market_value'], P),
        capital=d['capital'],
        cost=d['cost'],
        tax=d['tax'],
        slippoint=d['slippoint'],
        account_info=d['account_info'],
    )
    return account


def pos_generate(d: dict):
    """订单生成器"""
    pos = Position(
        code=d['code'],
        exchange=d['exchange'],
        account_id=d['account_id'],
        buy_date=d['buy_date'],
        volume=d['volume'],
        available=d['available'],
        buy_price=d['buy_price'],
        now_price=d['now_price'],
        profit=d['profit']
    )
    return pos


def new_order_generate(d: dict):
    """新订单生成器，提高了容错并简化了数据,也是接收订单数据的标准"""
    try:
        vol = d.get('vol', 0)
        volume = d.get('volume', vol)
        order = Order(
            code=d['code'],
            exchange=d['exchange'],
            account_id=d['account_id'],
            order_type=d['order_type'],
            order_price=d.get('order_price', 0),
            volume=volume,
            order_date=d['order_date'],
            order_time=d['order_time']
        )
        return order
    except Exception:
        raise ValueError("订单数据有误")


def order_generate(d: dict):
    """订单生成器"""
    try:
        order = Order(
            code=d['code'],
            exchange=d['exchange'],
            account_id=d['account_id'],
            order_id=d['order_id'],
            order_type=d['order_type'],
            price_type=d['price_type'],
            trade_type=d['trade_type'],
            order_price=d['order_price'],
            trade_price=d['trade_price'],
            volume=d['volume'],
            traded=d['traded'],
            status=d['status'],
            order_date=d['order_date'],
            order_time=d['order_time'],
            error_msg=d['error_msg']
        )
        return order
    except Exception:
        raise ValueError("订单数据有误")


def cancel_order_generate(token, order_id, *, code=None, exchange=None):
    """撤销订单生成器"""
    try:
        order = Order(
            code=code,
            exchange=exchange,
            account_id=token,
            order_id=order_id,
            order_type=OrderType.CANCEL.value,
        )
        return order
    except Exception:
        raise ValueError("订单数据有误")


def account_record_generate(d: dict):
    """账户记录生成器"""
    account_record = AccountRecord(
        account_id=d['account_id'],
        check_date=d['check_date'],
        assets=d['assets'],
        available=d['available'],
        market_value=d['market_value']
    )
    return account_record

def pos_record_generate(d: dict):
    """持仓记录生成器"""
    pos_record = PosRecord(
        code=d['code'],
        exchange=d['exchange'],
        account_id=d['account_id'],
        first_buy_date=d['first_buy_date'],
        last_sell_date=d['last_sell_date'],
        max_vol=d['max_vol'],
        buy_price_mean=d['buy_price_mean'],
        sell_price_mean=d['sell_price_mean'],
        profit=d['profit'],
        is_clear=d['is_clear']
    )
    return pos_record