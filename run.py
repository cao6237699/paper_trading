
import sys

from paper_trading.config import config
from paper_trading.app import creat_app
from paper_trading.trade.pt_engine import MainEngine
from paper_trading.utility.constant import ConfigType, PersistanceMode, LoadDataMode
from paper_trading.trade.market import (
    BacktestMarket,
    ChinaAMarket
)


def main():
    # 系统参数
    param = dict()
    market = None

    # 持久化参数， 默认实时模式
    param['PERSISTENCE_MODE'] = PersistanceMode.REALTIME
    # 数据加载参数，默认交易模式
    param['LOAD_DATA_MODE'] = LoadDataMode.TRADING

    # 模拟交易flask配置参数
    config_name = ConfigType.DEFAULT.value

    # 获取命令行输入的参数，判断启动何种模式的引擎
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            market = BacktestMarket
            param['PERSISTENCE_MODE'] = PersistanceMode.MANUAL
            param['LOAD_DATA_MODE'] = LoadDataMode.BACKTEST
            config_name = ConfigType.TESTING.value
        elif sys.argv[1] == "dev":
            market = BacktestMarket
            param['PERSISTENCE_MODE'] = PersistanceMode.MANUAL
            param['LOAD_DATA_MODE'] = LoadDataMode.BACKTEST
            config_name = ConfigType.DEVELOPMENT.value

    param['MONGO_HOST'] = config[config_name].MONGO_HOST
    param['MONGO_PORT'] = config[config_name].MONGO_PORT

    me = MainEngine(market=market, param=param)

    # 开启模拟交易引擎
    engine = me.start()
    if engine:
        host = config[config_name].SERVER_HOST
        port = config[config_name].SERVER_PORT
        debug = config[config_name].DEBUG
        app = creat_app(config_name, engine)

        app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()




