
import logging
import smtplib
from abc import ABC
from queue import Empty, Queue
from threading import Thread
from email.message import EmailMessage

from paper_trading.event import EventEngine, Event
from paper_trading.api.db import MongoDBService
from paper_trading.api.pytdx_api import PYTDXService
from paper_trading.utility.setting import SETTINGS
from paper_trading.utility.model import LogData
from paper_trading.utility.event import (
    EVENT_LOG,
    EVENT_ERROR,
    EVENT_MARKET_CLOSE
)
from paper_trading.utility.constant import PersistanceMode
from paper_trading.trade.market import ChinaAMarket
from paper_trading.trade.account_engine import AccountEngine



class MainEngine():
    """模拟交易主引擎"""
    def __init__(
            self,
            event_engine: EventEngine = None,
            market = None,
            param: dict = None
    ):
        # 绑定事件引擎
        if not event_engine:
            self.event_engine = EventEngine()
        else:
            self.event_engine = event_engine
        self.event_engine.start()

        self._settings = SETTINGS                   # 配置参数
        self.__active = False                       # 主引擎状态
        self.pst_active = None                      # 数据持久化开关
        self._market = market                       # 交易市场
        self.account_engine = None                  # 账户引擎
        self.order_put = None                       # 订单回调函数


        # 更新参数
        self._settings.update(param)


        # 开启日志引擎
        log = LogEngine(self.event_engine)
        log.register_event()

        # 开启邮件引擎
        # self.email = EmailEngine(self.event_engine)
        # self.email.start()

        # 市场模拟交易线程
        self._thread = Thread(target=self._run)

        # 注册事件监听
        self.event_register()

        self.write_log("模拟交易主引擎：初始化完毕")

    def event_register(self):
        """注册事件监听"""
        self.event_engine.register(EVENT_ERROR, self.process_error_event)
        self.event_engine.register(EVENT_MARKET_CLOSE, self.process_market_close)

    def start(self):
        """引擎初始化"""
        self.write_log("模拟交易主引擎：启动")

        # 引擎工作参数检查
        self._param_check()

        # 持久化配置
        if self._settings['PERSISTENCE_MODE'] == PersistanceMode.REALTIME:
            self.pst_active = True
        elif self._settings['PERSISTENCE_MODE'] == PersistanceMode.MANUAL:
            self.pst_active = False
        else:
            raise ValueError("持久化参数错误")

        # 连接数据库
        db = self.creat_db()

        # 连接行情
        hq_client = self.creat_hq_api()

        # 账户引擎启动
        self.account_engine = AccountEngine(self.event_engine,
                                            self.pst_active,
                                            self._settings['LOAD_DATA_MODE'],
                                            db)
        self.account_engine.start()

        # 默认使用ChinaAMarket
        if not self._market or isinstance(self._market, ChinaAMarket):
            self._market = ChinaAMarket(self.event_engine,
                                        self.account_engine,
                                        hq_client,
                                        {})
        else:
            self._market = self._market(self.event_engine,
                                        self.account_engine,
                                        hq_client,
                                        {})

        # 交易市场初始化，并返回订单推送函数
        self.order_put = self._market.on_init()

        # 启动订单薄撮合程序
        self._thread.start()
        self.__active = True

        return self

    def restart(self):
        """引擎初始化"""
        self.write_log("模拟交易主引擎：启动")

        # 引擎工作参数检查
        self._param_check()

        # 持久化配置
        if self._settings['PERSISTENCE_MODE'] == PersistanceMode.REALTIME:
            self.pst_active = True
        elif self._settings['PERSISTENCE_MODE'] == PersistanceMode.MANUAL:
            self.pst_active = False
        else:
            raise ValueError("持久化参数错误")

        # 连接数据库
        db = self.creat_db()

        # 连接行情
        hq_client = self.creat_hq_api()

        # 账户引擎启动
        self.account_engine = AccountEngine(self.event_engine,
                                            self.pst_active,
                                            self._settings['LOAD_DATA_MODE'],
                                            db)
        self.account_engine.start()

        # 默认使用ChinaAMarket
        if not self._market or isinstance(self._market, ChinaAMarket):
            self._market = ChinaAMarket(self.event_engine,
                                        self.account_engine,
                                        hq_client,
                                        {})
        else:
            self._market = self._market(self.event_engine,
                                        self.account_engine,
                                        hq_client,
                                        {})

        # 交易市场初始化，并返回订单推送函数
        self.order_put = self._market.on_init()

        # 启动订单薄撮合程序
        self._thread = Thread(target=self._run)
        self._thread.start()
        self.__active = True

        return self

    def _run(self):
        """订单薄撮合程序启动"""
        self._market.on_match()

    def _close(self):
        """模拟交易引擎关闭"""
        # 关闭市场
        self._market._active = False
        self._thread.join()

        self.__active = False

        self.write_log("模拟交易主引擎：关闭")

    def _param_check(self):
        """引擎工作参数检查"""
        if not self._settings['PERSISTENCE_MODE']:
            raise ValueError("数据持久化参数未配置")

    def on_orders_arrived(self, order):
        """订单到达处理"""
        if self.__active:
            status, msg = self.account_engine.orders_arrived(order)
            return status, msg
        else:
            return False, "交易市场关闭"

    def process_market_close(self, event):
        """市场关闭处理"""
        market_name = event.data
        self.write_log("{}: 交易市场闭市".format(market_name))
        self._close()

    def process_error_event(self, event):
        """系统错误处理"""
        msg = event.data
        self.write_log(msg, level=logging.CRITICAL)
        # self.email.queue.put(msg)

    def creat_db(self):
        """实例化数据库"""
        host = self._settings.get('MONGO_HOST', "localhost")
        port = self._settings.get('MONGO_PORT', 27017)
        db = MongoDBService(host, port)
        db.connect_db()
        return db

    def creat_hq_api(self):
        """实例化行情源"""
        tdx = PYTDXService()
        tdx.connect_api()

        return tdx

    def write_log(self, msg: str, level: int = logging.INFO):
        """"""
        log = LogData(
            log_content=msg,
            log_level=level
        )
        event = Event(EVENT_LOG, log)
        self.event_engine.put(event)


class Singleton(type):
    """
    Singleton metaclass,

    class A:
        __metaclass__ = Singleton
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """"""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class BaseEngine(ABC):
    """
    Abstract class for implementing an function engine.
    """

    def __init__(
            self,
            event_engine: EventEngine,
            engine_name: str,
    ):
        """"""
        self.event_engine = event_engine
        self.engine_name = engine_name

    def close(self):
        """"""
        pass


class LogEngine(BaseEngine):
    """
    Processes log event and output with logging module.
    """
    __metaclass__ = Singleton

    def __init__(self, event_engine: EventEngine):
        """"""
        super(LogEngine, self).__init__(event_engine, "log")

        if not SETTINGS["log.active"]:
            return

        self.level = SETTINGS["log.level"]
        self.logger = logging.getLogger("lazyTrader")
        self.logger.setLevel(self.level)
        self.formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        self.register_event()

    def add_null_handler(self):
        """
        Add null handler for logger.
        """
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self):
        """
        Add console output of log.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_log_event(self, event: Event):
        """
        Output log event data with logging function.
        """
        log = event.data
        self.logger.log(log.log_level, log.log_content)

    def close(self):
        """"""
        pass


class EmailEngine(BaseEngine):
    """
    邮件引擎
    """

    def __init__(self, event_engine: EventEngine):
        """"""
        super(EmailEngine, self).__init__(event_engine, "email")

        self.thread = Thread(target=self.run)
        self.queue = Queue()
        self.active = False

    def send_email(self, subject: str, content: str, receiver: str = ""):
        """"""
        # Start email engine when sending first email.
        if not self.active:
            self.start()

        # Use default receiver if not specified.
        if not receiver:
            receiver = SETTINGS["email.receiver"]

        msg = EmailMessage()
        msg["From"] = SETTINGS["email.sender"]
        msg["To"] = SETTINGS["email.receiver"]
        msg["Subject"] = subject
        msg.set_content(content)

        self.queue.put(msg)

    def run(self):
        """"""
        while self.active:
            try:
                msg = self.queue.get(block=True, timeout=1)

                with smtplib.SMTP_SSL(
                        SETTINGS["email.server"], SETTINGS["email.port"]
                ) as smtp:
                    smtp.login(
                        SETTINGS["email.username"], SETTINGS["email.password"]
                    )
                    smtp.send_message(msg)
            except Empty:
                pass

    def start(self):
        """"""
        self.active = True
        self.thread.start()

    def close(self):
        """"""
        if not self.active:
            return

        self.active = False
        self.thread.join()
