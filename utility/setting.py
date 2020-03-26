# 全局配置
import string
import random
from logging import DEBUG

SETTINGS = {
    # 市场名称
    "MARKET_NAME": "",

    # 账户token长度
    "TOKEN_LENGTH": 20,

    # 数据精确度
    "POINT": 2,

    # 是否开启成交量计算模拟
    # TODO 暂时没有实现相关功能
    "VOLUME_SIMULATION": False,

    # 是否开启账户与持仓信息的验证
    "VERIFICATION": True,

    # 引擎撮合速度（秒）
    # 设置此参数时请参考行情的刷新速度
    "PERIOD": 3,

    # 交易报告功能开关参数
    "IS_REPORT": True,

    # mongoDB 参数
    "MONGO_HOST": "",
    "MONGO_PORT": 0,
    "ACCOUNT_DB": "pt_account",
    "POSITION_DB": "pt_position",
    "TRADE_DB": "pt_trade",
    "ACCOUNT_RECORD": "pt_acc_record",
    "POS_RECORD": "pt_pos_record",

    # tushare行情源参数(填写你自己的tushare token，可以前往https://tushare.pro/ 注册申请)
    "TUSHARE_TOKEN": "3bd1ab27e003a6390baad5bd14292a0ab7d0c21983f8f6f176f51c6f",

    # pytdx行情参数（可以去各家券商下载通达信交易软件找到相关的地址）
    "TDX_HOST": "210.51.39.201",
    "TDX_PORT": 7709,

    # 账户初始参数
    "CAPITAL": 1000000.00,  # 初始资金
    "COST": 0.0003,         # 交易佣金
    "TAX": 0.001,           # 印花税
    "SLIPPOINT": 0.01,      # 滑点（暂未实现）

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
