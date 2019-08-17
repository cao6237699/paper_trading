
from datetime import datetime

try:
    import tushare as ts
except Exception as e:
    print(u'请先安装tushare模块')

from paper_trading.utility.setting import SETTINGS


class TushareService():
    """Tushare数据服务类"""

    def __init__(self):
        """Constructor"""
        self.connected = False  # 数据服务连接状态
        self.api = None  # 普通行情API
        self.pro_api = None  # 增强行情API

    def connect_api(self):
        """连接API"""
        # 连接增强行情API并检查连接情况
        try:
            token = SETTINGS['TUSHARE_TOKEN']
            self.pro_api = ts.pro_api(token)
            self.connected = True
            return True
        except BaseException:
            raise ConnectionError("tushare连接错误")

    def get_realtime_data(self, symbol: str):
        """获取股票实时数据"""
        code, exchange = symbol.split('.')
        try:
            df = ts.get_realtime_quotes(code)
            return df
        except ConnectionError:
            raise Exception("股票数据获取失败")

    @property
    def is_trade_date(self):
        """获取交易日期"""
        d = datetime.now().strftime("%Y%m%D")
        try:
            df = self.pro_api.trade_cal(
                exchange='SSE', start_date=d, end_date=d)
            if len(df):
                return True
            else:
                return False
        except ConnectionError:
            raise Exception("交易日信息获取失败")

    def close(self):
        """数据服务关闭"""
        self.connected = False
        self.api = None
        self.pro_api = None
