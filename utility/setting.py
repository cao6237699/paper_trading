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

    # 引擎的工作模式
    "ENGINE_MODE": EngineMode.REALTIME.value,

    # 交易报告功能开关参数
    "REPORT_MODE": True,

    # mongoDB 参数
    "MONGO_HOST": "",
    "MONGO_PORT": 0,
    "ACCOUNT_DB": "pt_account",
    "POSITION_DB": "pt_position",
    "TRADE_DB": "pt_trade",
    "MARKET_NAME": "",
    "REPORT_DB": "pt_report",

    # tushare行情源参数
    "TUSHARE_TOKEN": "fb579635d62cf964d6878551a6fd790620a044940db43a570b0da38c",

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
