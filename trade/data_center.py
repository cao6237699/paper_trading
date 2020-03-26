
import time
from datetime import datetime, timedelta

from paper_trading.utility.model import DBData

def get_stock_daily_qfq(symbol: str, start: str, end: str, db):
    """查询日线前复权数据"""
    # 前后各扩展10天
    start_date, end_date = date_extend(start, end, 10)

    raw_data = {}
    raw_data["flt"] = {'date': {'$gte': start_date, '$lte': end_date}}

    db_data = DBData(
        db_name="Stock_Daily_Db_Qfq",
        db_cl=symbol,
        raw_data=raw_data
    )
    result = list(db.on_select(db_data))
    data = []
    if result:
        for d in result:
            data.append([d['date'], d['open'], d['high'], d['low'], d['close'], d['volume']])
        return data
    else:
        return False

def get_stock_daily(symbol: str, start: str, end: str, ser):
    """获取日线数据"""
    pass

def get_stock_mtime(symbol: str, timestamp: int, ser):
    """获取分时数据"""
    date_array = datetime.utcfromtimestamp(timestamp)
    date = date_array.strftime("%Y%m%d")

    df = ser.get_history_transaction_data(symbol, timestamp)
    data = []
    if len(df):
        for i, row in df.iterrows():
            data.append([row['time'], row['price']])
        return data
    else:
        return False

def get_stock_K_line(symbol: str, start: str, end: str, freq: str):
    """获取k线数据"""
    pass

def date_extend(start: str, end: str, day: int):
    """日期扩展"""
    start_date = datetime.strptime(start, '%Y%m%d')
    end_date = datetime.strptime(end, '%Y%m%d')

    start_date = start_date - timedelta(days=day)
    end_date = end_date + timedelta(days=day)

    start_date = start_date.strftime('%Y%m%d')
    end_date = end_date.strftime('%Y%m%d')

    return start_date, end_date
