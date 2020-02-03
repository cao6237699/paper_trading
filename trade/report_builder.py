
import numpy as np
import pandas as pd

from paper_trading.utility.setting import SETTINGS
from paper_trading.utility.constant import Status, OrderType
from paper_trading.utility.model import DBData, AccountRecord


def calculate_result(token, db, start: str = None, end: str = None):
    """计算结果"""
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

    captial = account['captial']
    cost = account['cost']
    tax = account['tax']
    slipping = account['slipping']

    # 资产表
    account_df = load_account_record(token, db, captial, start, end)

    # 持仓表
    pos_df = load_pos(token, db)

    # 交易表
    trade_df = load_trade_record(token, db, cost, tax, start, end)

    return captial, account_df, pos_df, trade_df

def trade_statistics(captial, assets_df, pos_df, trade_df):
    """交易结果分析"""
    # 初始资金

    start_date = assets_df.iloc[0]['check_date']
    end_date = assets_df.iloc[-1]['check_date']

    total_days = len(assets_df)
    profit_days = len(assets_df[assets_df["net_pnl"] > 0])
    loss_days = len(assets_df[assets_df["net_pnl"] < 0])

    end_balance = float(assets_df.iloc[-1].assets)
    max_drawdown = round((assets_df['assets'].max() - assets_df['assets'].min()), 2)
    max_ddpercent = round((max_drawdown / assets_df['assets'].max()) * 100, 2)

    total_net_pnl = round((end_balance - captial), 2)
    total_commission = float(trade_df['commission'].sum())
    total_slippage = 0
    total_turnover = float(trade_df['volume'].sum())
    total_trade_count = len(trade_df)

    win_num = len(pos_df[pos_df.profit > 0])
    loss_num = len(pos_df[pos_df.profit <= 0])
    win_rate = round((win_num / (win_num + loss_num) * 100), 2)

    total_return = round(((end_balance / captial - 1) * 100), 2)
    annual_return = round((total_return / total_days * 240), 2)
    return_mean = pos_df['profit'].mean()
    return_std = pos_df['profit'].std()

    if return_std:
        sharpe_ratio = float(return_mean / return_std * np.sqrt(240))
    else:
        sharpe_ratio = 0

    statistics = {
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "profit_days": profit_days,
        "loss_days": loss_days,
        "captial": captial,
        "end_balance": end_balance,
        "max_drawdown": max_drawdown,
        "max_ddpercent": max_ddpercent,
        "total_net_pnl": total_net_pnl,
        "total_commission": total_commission,
        "total_slippage": total_slippage,
        "total_turnover": total_turnover,
        "total_trade_count": total_trade_count,
        "win_num": win_num,
        "loss_num": loss_num,
        "win_rate": win_rate,
        "total_return": total_return,
        "annual_return": annual_return,
        "daily_return": return_mean,
        "return_std": return_std,
        "sharpe_ratio": sharpe_ratio,
    }

    return statistics

def trade_record(trade_df):
    """交易记录"""
    for i, trade in trade_df.iterrows():
        print("订单编号：{}, 成交编号：{}, 交易日期：{}, 交易时间：{}, 证券代码：{}, 订单类型：{}, 成交价格：{}, 成交数量：{}".format(
            trade.order_id,
            trade.trade_id,
            trade.check_date,
            trade.time,
            trade.lz_symbol,
            trade.order_type.value,
            trade.price,
            trade.volume
        ))

def trade_chart():
    """交易结果图标展示"""
    pass

def pos_record(pos_df):
    """持仓"""
    pass

def account_daily_save(token, report_date, db):
    """资产每日记录"""
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

    try:
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
            db_name=SETTINGS['REPORT_DB'],
            db_cl=token,
            raw_data=raw_data
        )
        db.on_replace_one(db_data)
        return True
    except BaseException:
        return False

def load_account_record(token, db, captial, start: str = None, end: str = None):
    """加载资产记录"""
    raw_data = {}
    raw_data["flt"] = {'check_date': {'$gte': start, '$lte': end}}
    db_data = DBData(
        db_name=SETTINGS['REPORT_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    result = list(db.on_select(db_data))

    if not len(result):
        return False

    account_df = pd.DataFrame(result)

    # 计算net_pnl收益情况
    account_df['net_pnl'] = account_df['assets'] - captial

    return account_df

def load_pos(token, db):
    """加载持仓数据"""
    # 查询持仓数据
    raw_data = {}
    raw_data["flt"] = {}
    db_data = DBData(
        db_name=SETTINGS['POSITION_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    result = list(db.on_select(db_data))

    # 判断持仓是否为空
    if not len(result):
        return False

    # 将pos数据转换为dataframe数据
    pos_df = pd.DataFrame(result)

    return pos_df

def load_trade_record(token, db, cost, tax, start: str = None, end: str = None):
    """加载交易记录"""
    raw_data = {}
    raw_data["flt"] = {
                            'order_date': {'$gte': start, '$lte': end},
                            'status': Status.ALLTRADED.value
                       }
    db_data = DBData(
        db_name=SETTINGS['TRADE_DB'],
        db_cl=token,
        raw_data=raw_data
    )
    result = list(db.on_select(db_data))

    if not len(result):
        return

    trade_df = pd.DataFrame(result)
    trade_df['commission'] = 0.

    # 计算commission
    for i, row in trade_df.iterrows():
        commission = 0.
        if row['order_type'] == OrderType.BUY.value:
            commission = row['traded'] * row['trade_price'] * cost
        elif row['order_type'] == OrderType.SELL.value:
            commission = row['traded'] * row['trade_price'] * (cost + tax)
        else:
            pass

        trade_df.iloc[i]['commission'] = commission

    return trade_df
