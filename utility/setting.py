# 全局配置

import string
import random
from logging import CRITICAL, INFO, DEBUG
from paper_trading.utility.constant import EngineMode

SETTINGS = {
    # 账户token长度
    "TOKEN_LENGTH": 20,

    # 数据精确度
    "POINT": 2,

    # 模拟交易引擎模式
    # SIMULATION 不获取真实行情进行模拟交易，即时模拟成交
    # REALTIME 获取真实行情并进行模拟交易
    "ENGINE_MODE": EngineMode.REALTIME.value,

    # 是否开启成交量计算模拟
    # 引擎模式为SIMULATION下时，此参数失效
    # TODO 暂时没有实现相关功能
    "VOLUME_SIMULATION": False,

    # 是否开启账户与持仓信息的验证
    "VERIFICATION": True,

    # 引擎撮合速度（秒）
    # 引擎模式为SIMULATION下时，此参数失效
    # 设置此参数时请参考行情的刷新速度
    "PERIOD": 3,

    # 报告功能开关参数
    "REPORT_MODE": True,

    # mongoDB 参数
    "MONGO_HOST": "127.0.0.1",
    "MONGO_PORT": 27017,
    "ACCOUNT_DB": "pt_account",
    "POSITION_DB": "pt_position",
    "TRADE_DB": "pt_trade",
    "ORDERS_BOOK": "pt_orders_book",
    "MARKET_NAME": "",
    "REPORT": "pt_report",

    # tushare行情源参数
    "TUSHARE_TOKEN": "",

    # pytdx行情参数
    "TDX_HOST": "114.80.63.5",
    "TDX_PORT": 7709,

    # 账户初始参数
    "ASSETS": 1000000.00,   # 初始资金
    "COST": 0.0003,         # 交易佣金
    "TAX": 0.001,           # 印花税
    "SLIPPING": 0.01,       # 滑点 暂未实现

    # log服务参数
    "log.active": True,
    "log.level": DEBUG,
    "log.console": True,

    # email服务参数(根据实际情况进行使用）
    "email.server": "",
    "email.port": 0,
    "email.username": "",
    "email.password": "",
    "email.sender": "",
    "email.receiver": "",
}


def get_token():
    """生成账户token值"""
    w = string.ascii_letters + string.digits
    count = SETTINGS['TOKEN_LENGTH']
    token = []

    for i in range(count):
        token.append(random.choice(w))

    return "".join(token)
