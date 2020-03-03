
from pytdx.hq import TdxHq_API

from paper_trading.utility.setting import SETTINGS


# 市场代码对照表
exchange_map = {}
exchange_map['SH'] = 1
exchange_map['SZ'] = 0


class PYTDXService():
    """pytdx数据服务类"""

    def __init__(self):
        """Constructor"""
        self.connected = False  # 数据服务连接状态
        self.hq_api = None  # 行情API

    def connect_api(self):
        """连接API"""
        # 连接增强行情API并检查连接情况
        try:
            if not self.connected:
                host = SETTINGS["TDX_HOST"]
                port = SETTINGS["TDX_PORT"]
                self.hq_api = TdxHq_API()
                self.hq_api.connect(host, port)
                self.connected = True
            return True
        except Exception:
            raise ConnectionError("pytdx连接错误")

    def get_realtime_data(self, symbol: str):
        """获取股票实时数据"""
        try:
            symbols = self.generate_symbols(symbol)
            df = self.hq_api.to_df(self.hq_api.get_security_quotes(symbols))
            return df
        except Exception:
            raise ValueError("股票数据获取失败")

    @staticmethod
    def generate_symbols(symbol: str):
        """组装symbols数据，pytdx接收的是以市场代码和标的代码组成的元祖的list"""
        new_symbols = []
        code, exchange = symbol.split('.')
        new_symbols.append((exchange_map[exchange], code))

        return new_symbols

    def close(self):
        """数据服务关闭"""
        self.connected = False
        self.hq_api.disconnect()
