
import time
import pandas as pd
from datetime import datetime

from paper_trading.utility.setting import get_token, SETTINGS
from paper_trading.utility.constant import Status, OrderType, TradeType
from paper_trading.utility.model import Account, Position, Order, DBData
from paper_trading.trade.report_builder import (
    account_record_creat,
    pos_record_creat,
    pos_record_update_buy,
    pos_record_update_sell,
    pos_record_update_liq
)

# 小数点保留位数
P = SETTINGS["POINT"]

"""账户操作"""


def on_account_add(account_info: dict, db):
    """创建账户"""
    token = get_token()
    
    # 账户参数
    param = {
        'assets':SETTINGS['ASSETS'],
        'cost': SETTINGS['COST'],
        'tax': SETTINGS['TAX'],
        'slipping': SETTINGS['SLIPPING'],
        'info': ""
    }

    # 更新账户参数
    param.update(account_info)

    try:
        account = Account(
            account_id=token,
            assets=round(float(param['assets']), P),
            available=round(float(param['assets']), P),
            market_value=round(0.0, P),
            captial=round(float(param['assets']), P),
            cost=float(param['cost']),
            tax=float(param['tax']),
            slipping=float(param['slipping']),
            account_info=param['info']
        )

        raw_data = {}
        raw_data['flt'] = {'account_id': token}
        raw_data['data'] = account
        db_data = DBData(
            db_name=SETTINGS['ACCOUNT_DB'],
            db_cl=token,
            raw_data=raw_data
        )
        if db.on_insert(db_data):
            return token
    except BaseException:
        return False


def on_account_exist(token: str, db):
    """账户是否存在"""
    account = query_account_one(token, db)

    if account:
        return True
    else:
        return False


def on_account_delete(token: str, db):
    """账户删除"""
    try:
        account = DBData(
            db_name=SETTINGS['ACCOUNT_DB'],
            db_cl=token,
            raw_data={}
        )
        db.on_collection_delete(account)

        position = DBData(
            db_name=SETTINGS['POSITION_DB'],
            db_cl=token,
            raw_data={}
        )
        db.on_collection_delete(position)

        order = DBData(
            db_name=SETTINGS['TRADE_DB'],
            db_cl=token,
            raw_data={}
        )
        db.on_collection_delete(order)

        account_record = DBData(
            db_name=SETTINGS['ACCOUNT_RECORD'],
            db_cl=token,
            raw_data={}
        )
        db.on_collection_delete(account_record)

        pos_record = DBData(
            db_name=SETTINGS['POS_RECORD'],
            db_cl=token,
            raw_data={}
        )
        db.on_collection_delete(pos_record)

        return True
    except BaseException:
        return False


def on_account_update(order: Order, db):
    """订单成交后账户操作"""
    account = query_account_one(order.account_id, db)
    pos_val = query_position_value(order.account_id, db)

    if order.order_type == OrderType.BUY.value:
        on_account_buy(account, order, pos_val, db)
    else:
        on_account_sell(account, order, pos_val, db)


def on_account_buy(account: dict, order: Order, pos_val: float, db):
    """买入成交后账户操作"""
    frozen_all = account["assets"] - \
        account["available"] - account["market_value"]
    frozen = (order.volume * order.order_price) * (1 + account['cost'])
    pay = (order.traded * order.trade_price) * (1 + account['cost'])

    available = account["available"] + frozen - pay
    frozen_all = frozen_all - frozen
    assets = available + pos_val + frozen_all
    raw_data = {}
    raw_data["flt"] = {"account_id": account["account_id"]}
    raw_data["set"] = {'$set': {'available': round(available, P),
                                'assets': round(assets, P),
                                'market_value': round(pos_val, P)}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=account["account_id"],
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_account_sell(account: dict, order: Order, pos_val: float, db):
    """卖出成交后账户操作"""
    frozen = account["assets"] - account["available"] - account["market_value"]
    order_val = order.traded * order.trade_price
    cost = order_val * account['cost']
    tax = order_val * account['tax']
    available = account["available"] + order_val - cost - tax
    assets = available + pos_val + frozen

    raw_data = {}
    raw_data["flt"] = {"account_id": account["account_id"]}
    raw_data["set"] = {'$set': {'available': round(available, P),
                                'assets': round(assets, P),
                                'market_value': round(pos_val, P)}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=account["account_id"],
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_account_liquidation(db, token: str):
    """账户清算"""
    account = query_account_one(token, db)
    pos_val = query_position_value(token, db)

    # 解除冻结
    available = account["assets"] - account["market_value"]
    assets = available + pos_val

    raw_data = {}
    raw_data["flt"] = {"account_id": token}
    raw_data["set"] = {'$set': {'available': round(available, P),
                                'assets': round(assets, P),
                                'market_value': round(pos_val, P)}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    return db.on_update(db_data)


def query_account_list(db):
    """查询账户列表"""
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl="",
        raw_data={}
    )
    return db.on_collections_query(db_data)


def query_account_one(token: str, db):
    """查询账户信息"""
    if token:
        raw_data = {}
        raw_data['flt'] = {"account_id": token}
        db_data = DBData(
            db_name=SETTINGS['ACCOUNT_DB'],
            db_cl=token,
            raw_data=raw_data
        )
        account = db.on_query_one(db_data)
        if account:
            del account["_id"]
            return account
        else:
            return False


def query_account_record(token, db, start: str = None, end: str = None):
    """查询账户记录"""
    raw_data = {}
    raw_data["flt"] = {'check_date': {'$gte': start, '$lte': end}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    result = list(db.on_select(db_data))
    account_record = []
    if result:
        for i in result:
            del i["_id"]
            account_record.append(i)
        return account_record
    else:
        return False


"""订单操作"""


def on_orders_arrived(order: Order, db):
    """订单到达"""
    # 接收订单前的验证
    if SETTINGS['VERIFICATION']:
        result, msg = on_front_verification(order, db)
        if not result:
            return result, msg

    return on_orders_insert(order, db)


def on_orders_insert(order: Order, db):
    """订单插入"""
    order.order_id = str(time.time())
    token = order.account_id
    order.status = Status.NOTTRADED.value

    raw_data = {}
    raw_data['flt'] = {'order_id': order.order_id}
    raw_data['data'] = order
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )

    if db.on_replace_one(db_data):
        return True, order
    else:
        return False, "交易表新增订单失败"


def on_orders_exist(token: str, order_id: str, db):
    """查询订单是否存在"""
    raw_data = {}
    raw_data["flt"] = {'order_id': order_id}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    order = db.on_select(db_data)
    if order.count():
        return True
    else:
        return False


def on_order_update(order: Order, db):
    """订单状态更新"""
    result, order_old = query_order_one(order.account_id, order.order_id, db)

    raw_data = {}
    raw_data["flt"] = {'order_id': order.order_id}
    raw_data["set"] = {'$set': {'status': order.status,
                                'trade_type': order.trade_type,
                                'trade_price': order.trade_price,
                                'traded': (order.traded + order_old["traded"]),
                                'error_msg': order.error_msg}}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=order.account_id,
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_order_deal(order: Order, db):
    """订单成交处理"""
    # 持仓处理
    on_position_update(order, db)

    # 账户处理
    on_account_update(order, db)

    if order.volume == order.traded:
        order.status = Status.ALLTRADED.value
    else:
        order.status = Status.PARTTRADED.value

    on_order_update(order, db)


def query_order_status(token: str, order_id: str, db):
    """查询订单情况"""
    raw_data = {}
    raw_data["flt"] = {'order_id': order_id}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    order = db.on_query_one(db_data)

    if order:
        return True, order["status"]
    else:
        return False, "无此订单"


def query_orders(token: str, db):
    """查询交割单"""
    raw_data = {}
    raw_data["flt"] = {}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    result = db.on_select(db_data)
    orders = []

    if isinstance(result, bool):
        return False
    else:
        result = list(result)
        if result:
            for o in result:
                del o["_id"]
                orders.append(o)
            return orders
        else:
            return "无委托记录"


def query_order_one(token: str, order_id: str, db):
    """查询一条订单数据"""
    raw_data = {}
    raw_data["flt"] = {'order_id': order_id}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    order = db.on_query_one(db_data)

    if order:
        return True, order
    else:
        return False, ""


def query_orders_today(token: str, db):
    """查询今天的所有订单"""
    today = datetime.now().strftime("%Y%m%d")
    raw_data = {}
    raw_data["flt"] = {"order_date": today}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    result = db.on_select(db_data)
    orders = []

    if isinstance(result, bool):
        return False
    else:
        result = list(result)
        if result:
            for o in result:
                del o["_id"]
                orders.append(o)
            return orders
        else:
            return "无委托记录"

"""持仓操作"""


def query_position(token: str, db):
    """查询所有持仓信息"""
    raw_data = {}
    raw_data["flt"] = {}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    result = list(db.on_select(db_data))
    pos = []
    if isinstance(result, bool):
        return False
    else:
        result = list(result)
        if result:
            for p in result:
                del p["_id"]
                pos.append(p)
            return pos
        else:
            return "无持仓"


def query_position_one(token: str, symbol: str, db):
    """查询某一只证券的持仓"""
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': symbol}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    pos = db.on_query_one(db_data)
    if pos:
        return True, pos
    else:
        return False, ""


def query_position_value(token: str, db):
    """查询账户市值"""
    pos = query_position(token, db)

    if pos != "无持仓":
        df = pd.DataFrame(list(pos))
        df['value'] = (df['volume'] * df['now_price'])
        return float(df['value'].sum())
    else:
        return 0


def query_position_record(token, db, start: str = None, end: str = None):
    """查询账户记录"""
    raw_data = {}
    raw_data["flt"] = {'first_buy_date': {'$gte': start, '$lte': end}}
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    result = list(db.on_select(db_data))
    pos_record = []
    if result:
        for i in result:
            del i["_id"]
            pos_record.append(i)
        return pos_record
    else:
        return False


def on_position_insert(order: Order, cost: float, db):
    """持仓增加"""
    profit = cost * -1
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

    raw_data = {}
    raw_data['flt'] = {'pt_symbol': pos.pt_symbol}
    raw_data['data'] = pos
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=order.account_id,
        raw_data=raw_data
    )
    if db.on_insert(db_data):
        # 保存持仓记录
        return pos_record_creat(order.account_id, db, pos)


def on_position_update(order: Order, db):
    """订单成交后持仓操作"""
    if order.order_type == OrderType.BUY.value:
        on_position_append(order, db)
    else:
        on_position_reduce(order, db)


def on_position_append(order: Order, db):
    """持仓增长"""
    token = order.account_id
    symbol = order.pt_symbol

    # 查询账户信息
    account = query_account_one(token, db)

    result, pos_o = query_position_one(token, symbol, db)
    cost = order.volume * order.trade_price * account['cost']
    if result:
        volume = pos_o['volume'] + order.traded
        now_price = order.trade_price
        profit = (order.trade_price -
                  pos_o['now_price']) * pos_o['volume'] + pos_o['profit'] - cost
        available = pos_o['available'] + order.traded

        if order.trade_type == TradeType.T_PLUS1.value:
            available = pos_o['available']

        buy_price = round(((pos_o['volume'] *
                            pos_o['now_price']) +
                           (order.traded *
                            order.trade_price)) /
                          volume, 2)

        raw_data = {}
        raw_data["flt"] = {'pt_symbol': symbol}
        raw_data["set"] = {'$set': {'volume': round(volume, P),
                                    'available': round(available, P),
                                    'buy_price': round(buy_price, P),
                                    'now_price': round(now_price, P),
                                    'profit': round(profit, P)}}
        db_data = DBData(
            db_name=SETTINGS['POSITION_DB'],
            db_cl=token,
            raw_data=raw_data
        )
        if db.on_update(db_data):
            # 更新持仓记录
            pos_info = {
                "vol": round(order.traded, P),
                "buy_price": round(buy_price, P),
                "profit": round(profit, P)
            }
            return pos_record_update_buy(token, db, symbol, pos_info)

    else:
        on_position_insert(order, cost, db)


def on_position_reduce(order: Order, db):
    """持仓减少"""
    token = order.account_id
    symbol = order.pt_symbol

    # 查询账户信息
    account = query_account_one(token, db)

    result, pos_o = query_position_one(token, symbol, db)
    volume = pos_o['volume'] - order.volume
    now_price = order.trade_price
    cost = order.volume * order.trade_price * account['cost']
    tax = order.volume * order.trade_price * account['tax']
    profit = (order.trade_price - pos_o['now_price']) * \
        pos_o['volume'] + pos_o['profit'] - cost - tax

    raw_data = {}
    raw_data["flt"] = {'pt_symbol': symbol}
    raw_data["set"] = {'$set': {'volume': round(volume, P),
                                'now_price': round(now_price, P),
                                'profit': round(profit, P)}}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    if db.on_update(db_data):
        # 更新持仓记录
        pos_info = {
            "sell_price": round(now_price, P),
            "vol": round(order.volume, P),
            "profit": round(profit, P),
            "date": order.order_date
        }
        return pos_record_update_sell(token, db, symbol, pos_info)


def on_position_liquidation(db, token, price_dict: dict = None):
    """持仓清算"""
    pos_list = query_position(token, db)
    if isinstance(pos_list, list):
        for pos in pos_list:
            if price_dict:
                if pos["pt_symbol"] in price_dict.keys():
                    # 更新最新价格
                    new_price = price_dict.get(pos["pt_symbol"])
                    on_position_update_price(token, pos, new_price, db)
            # 解除账户冻结
            on_position_frozen_cancel(token, pos, db)


def on_position_update_price(token: str, pos: dict, price: float, db):
    """更新持仓价格并解除冻结"""
    volume = pos['volume']
    if volume:
        profit = (price - pos['now_price']) * \
            pos['volume'] + pos['profit']

        raw_data = {}
        raw_data["flt"] = {'pt_symbol': pos['pt_symbol']}
        raw_data["set"] = {'$set': {'now_price': round(price, P),
                                    'profit': round(profit, P),
                                    'available': volume}}
        db_data = DBData(
            db_name=SETTINGS['POSITION_DB'],
            db_cl=token,
            raw_data=raw_data
        )
        db.on_update(db_data)


def on_position_frozen_cancel(token: str, pos: dict, db):
    """持仓解除冻结"""
    volume = pos['volume']
    if volume:
        raw_data = {}
        raw_data["flt"] = {'pt_symbol': pos["pt_symbol"]}
        raw_data["set"] = {'$set': {'available': pos["volume"]}}
        db_data = DBData(
            db_name=SETTINGS['POSITION_DB'],
            db_cl=token,
            raw_data=raw_data
        )
        db.on_update(db_data)
    else:
        # 持仓为空的删除持仓信息
        raw_data = {}
        raw_data["flt"] = {'pt_symbol': pos["pt_symbol"]}
        db_data = DBData(
            db_name=SETTINGS['POSITION_DB'],
            db_cl=token,
            raw_data=raw_data
        )
        db.on_delete(db_data)

        # 持仓记录清算
        pos_record_update_liq(token ,db, pos['pt_symbol'])


"""验证操作"""


def on_front_verification(order: Order, db):
    """订单前置验证"""
    # 验证市场是否开启
    if not SETTINGS["MARKET_NAME"]:
        return False, "交易市场关闭"

    # 验证账户是否存在
    if not on_account_exist(order.account_id, db):
        return False, "账户不存在"

    # 对订单的准确性验证
    # TODO

    if order.order_type == OrderType.BUY.value:
        return account_verification(order, db)
    else:
        return position_verification(order, db)


def account_verification(order: Order, db):
    """订单账户资金验证"""
    token = order.account_id

    # 查询账户信息
    account = query_account_one(token, db)

    money_need = order.volume * order.order_price * (1 + account['cost'])

    if account['available'] >= money_need:
        on_buy_frozen(account, money_need, db)
        return True, ""
    else:
        return False, "账户资金不足"


def position_verification(order: Order, db):
    """订单持仓验证"""
    pos_need = order.volume
    result, pos = query_position_one(order.account_id, order.pt_symbol, db)

    if result:
        if pos['available'] >= pos_need:
            on_sell_frozen(pos, order.volume, db)
            return True, ""
        else:
            return False, "可用持仓不足"
    else:
        return False, "无可用持仓"


def on_buy_frozen(account, pay: float, db):
    """买入资金冻结"""
    available = account["available"] - pay
    raw_data = {}
    raw_data["flt"] = {'account_id': account["account_id"]}
    raw_data["set"] = {'$set': {'available': available}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=account["account_id"],
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_sell_frozen(pos, vol: float, db):
    """卖出证券冻结"""
    available = pos["available"] - vol
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': pos['pt_symbol']}
    raw_data["set"] = {'$set': {'available': available}}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=pos["account_id"],
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_order_cancel(token: str, order_id: str, db):
    """取消订单"""
    result, order = query_order_one(token, order_id, db)
    if result:
        order = order_generate(order)
        order.status = Status.CANCELLED.value
        on_order_refuse(order, db)


def on_order_refuse(order: Order, db):
    """订单被拒绝"""
    on_order_update(order, db)

    if order.order_type == OrderType.BUY.value:
        return on_buy_cancel(order, db)
    else:
        return on_sell_cancel(order, db)


def on_buy_cancel(order: Order, db):
    """买入订单取消"""
    token = order.account_id

    # 查询账户信息
    account = query_account_one(token, db)

    pay = (order.volume - order.traded) * \
        order.order_price * (1 + account['cost'])

    available = account["available"] + pay
    raw_data = {}
    raw_data["flt"] = {'account_id': token}
    raw_data["set"] = {'$set': {'available': available}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_sell_cancel(order: Order, db):
    """卖出取消"""
    result, pos = query_position_one(order.account_id, order.pt_symbol, db)
    available = pos["available"] + order.volume - order.traded
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': pos["pt_symbol"]}
    raw_data["set"] = {'$set': {'available': available}}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=pos["account_id"],
        raw_data=raw_data
    )
    return db.on_update(db_data)


"""清算操作"""


def on_liquidation(db, token: str, check_date: str, price_dict: dict = None):
    """清算"""
    # 更新所有持仓最新价格和冻结证券
    on_position_liquidation(db, token, price_dict)

    # 更新账户市值和冻结资金
    on_account_liquidation(db, token)

    # 账户记录
    account_record_creat(token, check_date, db)

    return True


def order_generate(d: dict):
    """订单生成器"""
    try:
        order = Order(
            code=d['code'],
            exchange=d['exchange'],
            account_id=d['account_id'],
            order_id=d['order_id'],
            product=d['product'],
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


def cancel_order_generate(token ,order_id):
    """撤销订单生成器"""
    try:
        order = Order(
            code="",
            exchange="",
            account_id=token,
            order_id=order_id,
            order_type=OrderType.CANCEL.value
        )
        return order
    except Exception:
        raise ValueError("订单数据有误")


def liq_order_generate(token ,symbol, price, check_date):
    """清算订单生成器"""
    try:
        code, exchange = symbol.split('.')
        order = Order(
            code=code,
            exchange=exchange,
            account_id=token,
            order_price=price,
            order_type=OrderType.LIQ.value,
            order_date=check_date
        )
        return order
    except Exception:
        raise ValueError("订单数据有误")

