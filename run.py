import sys

from paper_trading.config import config
from paper_trading.app import creat_app
from paper_trading.utility.setting import SETTINGS
from paper_trading.trade.pt_engine import MainEngine
from paper_trading.utility.constant import EngineMode, ConfigType


def main():
    # 引擎参数
    param = dict()

    # 模拟交易引擎模式
    # SIMULATION 不获取真实行情进行模拟交易，即时模拟成交
    # REALTIME 获取真实行情并进行模拟交易(此为默认)
    mode = SETTINGS.get('ENGINE_MODE')
    config_name = ConfigType.DEFAULT.value

    # 获取命令行输入的参数，判断启动何种模式的引擎
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            mode = EngineMode.SIMULATION.value
            config_name = ConfigType.TESTING.value

    param['MONGO_HOST'] = config[config_name].MONGO_HOST
    param['MONGO_PORT'] = config[config_name].MONGO_PORT
    param['ENGINE_MODE'] = mode

    me = MainEngine(param=param)

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




