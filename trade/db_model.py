
import copy
from datetime import datetime

from paper_trading.utility.setting import get_token, SETTINGS
from paper_trading.utility.model import (
    Account,
    Position,
    Order,
    DBData
)

# 小数点保留位数
P = SETTINGS["POINT"]

"""账户操作"""


def on_account_add(account_info: dict, db):
    """创建账户"""
    token = get_token()

    # 账户参数
    param = {
        'capital': SETTINGS['CAPITAL'],
        'cost': SETTINGS['COST'],
        'tax': SETTINGS['TAX'],
        'slippoint': SETTINGS['SLIPPOINT'],
        'info': ""
    }

    # 更新账户参数
    param.update(account_info)

    account = Account(
        account_id=token,
        assets=round(float(param['capital']), P),
        available=round(float(param['capital']), P),
        market_value=round(0.0, P),
        capital=round(float(param['capital']), P),
        cost=float(param['cost']),
        tax=float(param['tax']),
        slippoint=float(param['slippoint']),
        account_info=param['info']
    )
    account_dict = copy.copy(account.__dict__)

    raw_data = {}
    raw_data['flt'] = {'account_id': token}
    raw_data['data'] = account
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    if db.on_insert(db_data):
        return account_dict


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


def on_account_update(data: dict, db):
    """账户更新"""
    raw_data = {}
    raw_data["flt"] = {"account_id": data["token"]}
    raw_data["set"] = {'$set': {'available': data["avl"],
                                'assets': data["assets"],
                                'market_value': data["market_value"]}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=data["token"],
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_account_avl_update(data: dict, db):
    """账户可用资金更新"""
    raw_data = {}
    raw_data["flt"] = {'account_id': data['token']}
    raw_data["set"] = {'$set': {'available': data['avl']}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=data['token'],
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_account_assets_update(data: dict, db):
    """账户资产更新"""
    raw_data = {}
    raw_data["flt"] = {"account_id": data["token"]}
    raw_data["set"] = {'$set': {'assets': data["assets"],
                                'market_value': data["market_value"]}}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=data["token"],
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


"""订单操作"""


def on_orders_insert(order: Order, db):
    """订单插入"""
    raw_data = {}
    raw_data['flt'] = {'order_id': order.order_id}
    raw_data['data'] = order
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=order.account_id,
        raw_data=raw_data
    )

    if db.on_replace_one(db_data):
        return True, ""
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


def on_orders_insert_many(token, order_list, db):
    """批量保存订单数据"""
    raw_data = {}
    raw_data['flt'] = {}
    raw_data['data'] = order_list
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    return db.on_insert_many(db_data)


def on_orders_clear(token, db):
    """订单数据清空"""
    raw_data = {}
    raw_data['flt'] = {}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    db.on_collection_delete(db_data)


def on_order_update(order: Order, db):
    """订单数据更新"""
    raw_data = {}
    raw_data["flt"] = {'order_id': order.order_id}
    raw_data["set"] = {'$set': {'status': order.status,
                                'trade_type': order.trade_type,
                                'trade_price': order.trade_price,
                                'traded': order.traded,
                                'error_msg': order.error_msg}}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=order.account_id,
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_order_status_update(data, db):
    """订单状态更新"""
    raw_data = {}
    raw_data["flt"] = {'order_id': data['id']}
    raw_data["set"] = {'$set': {'status': data['status'],
                                'error_msg': data['msg']}}
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=data['token'],
        raw_data=raw_data
    )
    return db.on_update(db_data)


def query_orders(token: str, db, flt: dict = None):
    """查询交割单"""
    raw_data = {}
    raw_data["flt"] = flt or {}
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
            return False


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
            return False


def query_orders_by_symbol(token: str, symbol: str, db):
    """查询某symbol的所有订单"""
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': symbol}
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
            return "无此代码的交易记录"


"""持仓操作"""


def on_position_insert(pos: Position, db):
    """持仓增加"""
    raw_data = {}
    raw_data['flt'] = {'pt_symbol': pos.pt_symbol}
    raw_data['data'] = pos
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=pos.account_id,
        raw_data=raw_data
    )
    db.on_insert(db_data)


def on_position_delete(data: dict, db):
    """持仓删除事件"""
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': data["symbol"]}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=data['token'],
        raw_data=raw_data
    )
    db.on_delete(db_data)


def on_position_clear(token: str, db):
    """持仓清空事件"""
    raw_data = {}
    raw_data['flt'] = {}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    db.on_collection_delete(db_data)


def on_position_update(pos: Position, db):
    """持仓更新"""
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': pos.pt_symbol}
    raw_data["set"] = {'$set': {'volume': pos.volume,
                                'available': pos.available,
                                'buy_price': pos.buy_price,
                                'now_price': pos.now_price,
                                'profit': pos.profit}}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=pos.account_id,
        raw_data=raw_data
    )
    db.on_update(db_data)


def on_position_avl_update(data: dict, db):
    """可用证券更新"""

    raw_data = {}
    raw_data["flt"] = {'pt_symbol': data['symbol']}
    raw_data["set"] = {'$set': {'available': data['avl']}}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=data['token'],
        raw_data=raw_data
    )
    return db.on_update(db_data)


def on_position_price_update(data: dict, db):
    """更新持仓价格"""
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': data['symbol']}
    raw_data["set"] = {'$set': {'now_price': data['price'],
                                'profit': data['profit']}}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=data['token'],
        raw_data=raw_data
    )
    db.on_update(db_data)


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
            return False


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


"""账户记录"""


def account_record_creat(account_record, db):
    """资产每日记录"""
    raw_data = {}
    raw_data['flt'] = {'check_date': account_record.check_date}
    raw_data['data'] = account_record
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_RECORD'],
        db_cl=account_record.account_id,
        raw_data=raw_data
    )
    db.on_replace_one(db_data)

def account_record_insert_many(token, record_list, db):
    """批量保存账户记录数据"""
    raw_data = {}
    raw_data['flt'] = {}
    raw_data['data'] = record_list
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    return db.on_insert_many(db_data)

def account_record_clear(token, db):
    """账户记录清空"""
    raw_data = {}
    raw_data['flt'] = {}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    db.on_collection_delete(db_data)

def query_account_record(token, db, start: str = None, end: str = None):
    """查询账户记录"""
    raw_data = {}
    raw_data['flt'] = {}
    if start and end == None:
        raw_data["flt"] = {'first_buy_date': {'$gte': start}}
    elif start == None and end:
        raw_data["flt"] = {'first_buy_date': {'$lte': end}}
    elif start and end:
        raw_data["flt"] = {'first_buy_date': {'$gte': start, '$lte': end}}
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


"""持仓记录"""


def pos_record_creat(pos_record, db):
    """创建持仓记录"""
    raw_data = {}
    raw_data['flt'] = {}
    raw_data['data'] = pos_record
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=pos_record.account_id,
        raw_data=raw_data
    )
    return db.on_insert(db_data)

def pos_record_insert_many(token, record_list, db):
    """批量保存持仓记录数据"""
    raw_data = {}
    raw_data['flt'] = {}
    raw_data['data'] = record_list
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    return db.on_insert_many(db_data)

def pos_record_clear(token, db):
    """持仓记录清空"""
    raw_data = {}
    raw_data['flt'] = {}
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    db.on_collection_delete(db_data)

def pos_record_update_buy(data, db):
    """更新持仓记录--买入加仓"""
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': data['symbol'], 'is_clear': 0}
    raw_data["set"] = {'$set': {'max_vol': data['max_vol'],
                                'buy_price_mean': data['buy_price_mean'],
                                'profit': data['profit']}}
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=data['token'],
        raw_data=raw_data
    )
    return db.on_update(db_data)

def pos_record_update_sell(data, db):
    """更新持仓记录--卖出减仓"""
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': data['symbol'], 'is_clear': 0}
    raw_data["set"] = {'$set': {'sell_price_mean': data['sell_price_mean'],
                                'profit': data['profit'],
                                'last_sell_date': data['date']}}
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=data['token'],
        raw_data=raw_data
    )
    return db.on_update(db_data)

def pos_record_update_liq(data, db):
    """更新持仓记录--清仓"""
    raw_data = {}
    raw_data["flt"] = {'pt_symbol': data['symbol'], 'is_clear': 0}
    raw_data["set"] = {'$set': {'is_clear': 1}}
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=data['token'],
        raw_data=raw_data
    )
    return db.on_update(db_data)

def query_pos_record_one(token ,db, flt):
    """获取持仓记录"""
    raw_data = {}
    raw_data['flt'] = flt
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    pos_record = db.on_query_one(db_data)
    if pos_record:
        return pos_record
    else:
        return False

def query_pos_records(token , db, start: str = None, end: str = None):
    """获取持仓记录"""
    raw_data = {}
    raw_data["flt"] = {}

    if start and end == None:
        raw_data["flt"] = {'first_buy_date': {'$gte': start}}
    elif start == None and end:
        raw_data["flt"] = {'first_buy_date': {'$lte': end}}
    elif start and end:
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

def query_pos_records_not_clear(token ,db):
    """获取未清仓的持仓记录"""
    raw_data = {}
    raw_data['flt'] = {'is_clear': 0}
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
