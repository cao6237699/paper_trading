
from paper_trading.event import EVENT_TIMER

# 系统相关事件
EVENT_LOG = 'e_log'                         # 日志记录的事件
EVENT_ERROR = 'e_error'                     # 错误事件，api连接错误或者数据库错误

# 应用相关
EVENT_MARKET_CLOSE = "e_market_close"           # 市场关闭事件
EVENT_ACCOUNT_UPDATE = "e_a_u"                  # 账户更新事件
EVENT_ACCOUNT_AVL_UPDATE = "e_a_avl_u"          # 账户可用资金修改事件
EVENT_ACCOUNT_ASSETS_UPDATE = "e_a_assets_u"    # 账户资产修改事件
EVENT_POS_INSERT = "e_p_i"                      # 持仓保存事件
EVENT_POS_UPDATE = "e_p_u"                      # 持仓更新事件
EVENT_POS_AVL_UPDATE = "e_p_a_u"                # 卖出可用股份修改事件
EVENT_POS_PRICE_UPDATE = "e_p_p_u"              # 卖出可用股份修改事件
EVENT_POS_DELETE = "e_p_d"                      # 卖出可用股份修改事件
EVENT_ORDER_INSERT = "e_o_i"                    # 订单保存事件
EVENT_ORDER_UPDATE = "e_o_u"                    # 订单更新事件
EVENT_ORDER_STATUS_UPDATE = "e_o_s_u"           # 订单状态更新事件
EVENT_ORDER_DEAL = "e_o_d"                      # 订单成交事件
EVENT_ORDER_REJECTED = "e_o_r"                  # 订单拒绝事件
EVENT_ORDER_CANCELED = "e_o_c"                  # 订单取消事件
EVENT_ACCOUNT_RECORD_INSERT = "e_a_r_i"         # 账户记录建立事件
EVENT_POS_RECORD_INSERT = "e_p_r_i"             # 持仓记录修改事件
EVENT_POS_RECORD_BUY = "e_p_r_b"                # 持仓记录修改事件
EVENT_POS_RECORD_SELL = "e_p_r_s"               # 持仓记录修改事件
EVENT_POS_RECORD_CLEAR = "e_p_r_c"              # 持仓记录清理事件




