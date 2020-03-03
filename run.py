
import sys

from paper_trading.config import config
from paper_trading.app import creat_app
from paper_trading.trade.pt_engine import MainEngine
from paper_trading.utility.constant import ConfigType
from paper_trading.trade.market import (
    BacktestMarket,
    ChinaAMarket
)


def main():
    # 系统参数
    param = dict()
    market = None

    # 模拟交易flask配置参数
    config_name = ConfigType.DEFAULT.value

    # 获取命令行输入的参数，判断启动何种模式的引擎
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            market = BacktestMarket
            config_name = ConfigType.TESTING.value

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




