
from logging import INFO
from datetime import datetime
from dataclasses import dataclass

from paper_trading.utility.constant import Status


@dataclass
class BaseData(object):
    """
    数据的基础类，其他数据类继承于此
    """
    pass


@dataclass
class DBData(BaseData):
    """数据库数据类"""
    db_name: str        # 数据库名称
    db_cl: str          # 表名称
    raw_data: dict      # 原始数据


@dataclass
class LogData(BaseData):
    """日志数据类"""
    log_content: str  # 日志信息
    log_level: int = INFO  # 日志级别

    def __post_init__(self):
        self.log_time = datetime.now()  # 日志生成时间


@dataclass
class Account(BaseData):
    """账户数据类"""
    account_id: str          # 账户编号
    assets: float = 0        # 总资产
    available: float = 0     # 可用资金
    market_value: float = 0  # 总市值
    captial: float = 0       # 初始资金
    cost: float = 0          # 佣金
    tax: float = 0           # 税金
    slipping: float = 0      # 滑点
    account_info: str = ""   # 账户描述信息


@dataclass
class AccountRecord(BaseData):
    """账户数据记录"""
    account_id: str          # 账户编号
    check_date: str          # 检查点日期
    assets: float = 0        # 总资产
    available: float = 0     # 可用资金
    market_value: float = 0  # 总市值


@dataclass
class Position(BaseData):
    """持仓数据类"""
    code: str
    exchange: str
    account_id: str          # 账户编号
    buy_date: str = 0        # 买入日期
    volume: float = 0        # 总持仓
    available: float = 0     # 可用持仓
    buy_price: float = 0     # 买入均价
    now_price: float = 0     # 当前价格
    profit: float = 0        # 收益

    def __post_init__(self):
        """"""
        self.pt_symbol = f"{self.code}.{self.exchange}"


@dataclass
class PosRecord(BaseData):
    """持仓记录"""
    code: str
    exchange: str
    account_id: str                 # 账户编号
    first_buy_date: str             # 首次买入日期
    last_sell_date: str             # 最后卖出日期
    max_vol: float = 0              # 最大持仓量
    buy_price_mean: float = 0       # 买入均价
    sell_price_mean: float = 0      # 卖出均价
    profit: float = 0               # 收益
    is_clear: int = 0               # 是否清仓

    def __post_init__(self):
        """"""
        self.pt_symbol = f"{self.code}.{self.exchange}"


@dataclass
class Order(BaseData):
    """订单数据类"""
    code: str
    exchange: str
    account_id: str                           # 账户编号
    order_id: str = ""                        # 订单编号
    product: str = ""                         # 产品类型 股票、期货等
    order_type: str = ""                      # 订单类型 buy、sell等
    price_type: str = ""                      # 价格类型 limit、market等
    trade_type: str = ""                      # 交易类型 t0、t1等
    order_price: float = 0
    trade_price: float = 0
    volume: float = 0
    traded: float = 0
    status: Status = Status.SUBMITTING.value
    order_date: str = ""
    order_time: str = ""
    error_msg: str = ""

    def __post_init__(self):
        """"""
        self.pt_symbol = f"{self.code}.{self.exchange}"
