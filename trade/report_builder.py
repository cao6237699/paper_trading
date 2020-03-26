
from paper_trading.utility.setting import SETTINGS
from paper_trading.utility.model import DBData, AccountRecord, PosRecord

# 小数点保留位数
P = SETTINGS["POINT"]

# 报告开关
is_report = SETTINGS["IS_REPORT"]

"""账户记录"""

def account_record_creat(token, report_date, db):
    """资产每日记录"""
    if not is_report:
        return True

    # 查询账户信息
    raw_data = {}
    raw_data['flt'] = {"account_id": token}
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    account = db.on_query_one(db_data)

    if not account:
        return False

    # 创建每日账户记录
    account_daily = AccountRecord(
        account_id=account['account_id'],
        check_date=report_date,
        assets=account['assets'],
        available=account['available'],
        market_value=account['market_value']
    )
    raw_data = {}
    raw_data['flt'] = {'check_date': report_date}
    raw_data['data'] = account_daily
    db_data = DBData(
        db_name=SETTINGS['ACCOUNT_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    db.on_replace_one(db_data)


"""持仓记录"""

def pos_record_creat(token, db, pos):
    """创建持仓记录"""
    if not is_report:
        return True

    pos_record = PosRecord(
        code=pos.code,
        exchange=pos.exchange,
        account_id=token,
        first_buy_date=pos.buy_date,
        last_sell_date="",
        max_vol=pos.volume,
        buy_price_mean=pos.buy_price,
        sell_price_mean=0.0,
        profit=pos.profit
    )
    raw_data = {}
    raw_data['flt'] = {}
    raw_data['data'] = pos_record
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    return db.on_insert(db_data)

def pos_record_update_buy(token , db, symbol, pos: dict):
    """更新持仓记录--买入加仓"""
    if not is_report:
        return True

    # 查询持仓记录
    flt = {'pt_symbol': symbol, 'is_clear': 0}
    data = query_pos_record_one(token, db, flt)
    if data:
        new_max_vol = data['max_vol'] + pos['vol']
    else:
        raise ValueError("持仓记录不存在")

    raw_data = {}
    raw_data["flt"] = flt
    raw_data["set"] = {'$set': {'max_vol': new_max_vol,
                                'buy_price_mean': pos['buy_price'],
                                'profit': pos['profit']}}
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    return db.on_update(db_data)

def pos_record_update_sell(token, db, symbol, pos):
    """更新持仓记录--卖出减仓"""
    if not is_report:
        return True

    query_flt = {'pt_symbol': symbol, 'is_clear': 0}
    data = query_pos_record_one(token, db, query_flt)
    if data:
        max_vol = data['max_vol']
        sell_price = data['sell_price_mean'] + ((pos['vol'] / max_vol) * pos['sell_price'])
    else:
        raise ValueError("持仓记录不存在")

    raw_data = {}
    raw_data["flt"] = {'pt_symbol': symbol, 'is_clear': 0}
    raw_data["set"] = {'$set': {'sell_price_mean': round(sell_price, P),
                                'profit': pos['profit'],
                                'last_sell_date': pos['date']}}
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=token,
        raw_data=raw_data
    )
    return db.on_update(db_data)

def pos_record_update_liq(token, db, symbol):
    """更新持仓记录--清仓"""
    if not is_report:
        return True

    raw_data = {}
    raw_data["flt"] = {'pt_symbol': symbol, 'is_clear': 0}
    raw_data["set"] = {'$set': {'is_clear': 1}}
    db_data = DBData(
        db_name=SETTINGS['POS_RECORD'],
        db_cl=token,
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