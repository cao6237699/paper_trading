import os

from paper_trading.utility.constant import ConfigType
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or "j1as78a1gf6a4ea1f5d6a78e41fa56e"

    @staticmethod
    def init_app(app):
        pass

class TradingConfig(Config):
    MONGO_HOST = "192.168.1.254"
    MONGO_PORT = 27017
    LOG_FILE_NAME = ""
    LOG_FILE_PATH = ""
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5000


class TestingConfig(Config):
    MONGO_HOST = "localhost"
    MONGO_PORT = 27017
    LOG_FILE_NAME = ""
    LOG_FILE_PATH = ""
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5001

class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_HOST = "localhost"
    MONGO_PORT = 27017
    LOG_FILE_NAME = ""
    LOG_FILE_PATH = ""
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5001


config = {
    ConfigType.TESTING.value: TestingConfig,
    ConfigType.TRADING.value: TradingConfig,
    ConfigType.DEVELOPMENT.value: DevelopmentConfig,
    ConfigType.DEFAULT.value: TradingConfig
}