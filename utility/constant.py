from enum import Enum


class EngineMode(Enum):
    """模拟交易引擎模式"""
    REALTIME = "realtime"
    SIMULATION = "simulation"


class OrderType(Enum):
    """订单类型"""
    BUY = "buy"
    SELL = "sell"


class TradeType(Enum):
    """交易类型"""
    T_PLUS1 = "t1"
    T_PLUS0 = "t0"


class Direction(Enum):
    """
    Direction of order/trade/position.
    """
    LONG = "多"
    SHORT = "空"
    NET = "净"


class Offset(Enum):
    """
    Offset of order/trade.
    """
    NONE = ""
    OPEN = "开"
    CLOSE = "平"
    CLOSETODAY = "平今"
    CLOSEYESTERDAY = "平昨"


class Status(Enum):
    """
    Order status.
    """
    SUBMITTING = "提交中"
    NOTTRADED = "未成交"
    PARTTRADED = "部分成交"
    ALLTRADED = "全部成交"
    CANCELLED = "已撤销"
    REJECTED = "拒单"


class Product(Enum):
    """
    Product class.
    """
    EQUITY = "股票"
    FUTURES = "期货"
    OPTION = "期权"
    INDEX = "指数"
    FOREX = "外汇"
    SPOT = "现货"
    ETF = "ETF"
    BOND = "债券"
    WARRANT = "权证"


class PriceType(Enum):
    """
    Order price type.
    """
    LIMIT = "限价"
    MARKET = "市价"
    FAK = "FAK"
    FOK = "FOK"


class Exchange(Enum):
    """
    Exchange.
    """
    # Chinese
    CFX = "CFX"
    CFE = "CFE"
    SHF = "SHF"
    CZCE = "CZCE"
    DCE = "DCE"
    INE = "INE"
    SH = "SH"
    SZ = "SZ"
    SGE = "SGE"
