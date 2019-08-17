
from paper_trading.event import EVENT_TIMER

# 系统相关事件
EVENT_LOG = 'e_log'                       # 日志记录的事件
EVENT_ERROR = 'e_error'                   # 错误事件，api连接错误或者数据库错误

# 应用相关
EVENT_MARKET_CLOSE = "e_market_close"     # 订单成交事件
EVENT_ORDER_DEAL = "e_order_deal"         # 订单成交事件
EVENT_ORDER_REJECTED = "e_order_rejected" # 订单成交事件
