
import json
import requests
from datetime import datetime

SETTINGS = {
    "MARKET_URL": "",
    "MARKET_PORT": "",
    "MARKET_TIMEOUT": ""
}


class PaperTrading():
    """模拟交易"""

    def __init__(self, token: str = None, info: str = ""):
        self.home = ':'.join([SETTINGS["MARKET_URL"], SETTINGS["MARKET_PORT"]])

        # 连接模拟交易所
        result, msg = self.connect()

        if not result:
            self.connected = False
            raise ConnectionError(msg)

        self._token = token

        if not token:
            self._token = self.creat(info)

        self.connected = True

    def get_token(self):
        """获取token"""
        return self._token

    def get_url(self, method_name:str):
        """生成url"""
        return "/".join([self.home, method_name])

    def connect(self):
        """连接模拟交易程序"""
        url = self.get_url("")
        r = requests.get(url, timeout=SETTINGS["MARKET_TIMEOUT"])
        if r.status_code == requests.codes.ok:
            return True, ""
        else:
            return False, "模拟交易连接失败"

    def url_request(func):
        """请求函数的装饰器"""
        def wrapper(self, *args, **kwargs):
            if not self.connect():
                return False, "模拟交易服务连接失败"

            r = func(self, *args, **kwargs)

            if r.status_code == requests.codes.ok:
                d = json.loads(r.text)

                if d["status"]:
                    return True, d["data"]
                else:
                    return False, d["data"]
            else:
                return False, "请求状态不正确"

        return wrapper

    @url_request
    def creat(self, info):
        """创建模拟交易账户"""
        url = self.get_url("creat")
        data = {'info': info}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        if r.status_code == requests.codes.ok:
            d = json.loads(r.text)
            if d["status"]:
                self._token = d["data"]

        return r

    @url_request
    def delete(self):
        """删除模拟交易账户"""
        url = self.get_url("delete")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def get_list(self):
        """查询账户列表"""
        url = self.get_url("list")
        r = requests.get(url, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def account(self):
        """查询账户信息"""
        url = self.get_url("account")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def pos(self):
        """查询持仓信息"""
        url = self.get_url("pos")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def orders(self):
        """查询交割单信息"""
        url = self.get_url("orders")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def orders_today(self):
        """查询交割单信息"""
        url = self.get_url("orders_today")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def order_send(self, order):
        """发单"""
        if isinstance(order, dict):
            order = json.dumps(order)
            order.encode("utf-8")
        url = self.get_url("send")
        data = {"order": order}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def order_cancel(self, order_id):
        """撤单"""
        url = self.get_url("cancel")
        data = {'token': self._token, "order_id": order_id}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def order_status(self, order_id):
        """查询订单状态"""
        url = self.get_url("status")
        data = {'token': self._token, "order_id": order_id}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def liquidation(self, check_date: str, price_dict: dict):
        """清算"""
        price_dict_data = json.dumps(price_dict)
        url = self.get_url("liquidation")
        data = {'token': self._token, 'check_date': check_date, "price_dict": price_dict_data.encode("utf-8")}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    @url_request
    def report(self, start: str, end: str):
        """查询报告"""
        url = self.get_url("report")
        data = {'token': self._token, 'start': start, 'end': end}
        r = requests.post(url, data, timeout=SETTINGS["MARKET_TIMEOUT"])
        return r

    def show_report(self, report_dict: dict):
        """显示报告"""
        # 数据分析报告
        self.output("-" * 30)
        self.output(f"首个交易日：\t{report_dict['start_date']}")
        self.output(f"最后交易日：\t{report_dict['end_date']}")

        self.output(f"总交易日：\t{report_dict['total_days']}")
        self.output(f"盈利交易日：\t{report_dict['profit_days']}")
        self.output(f"亏损交易日：\t{report_dict['loss_days']}")

        self.output(f"起始资金：\t{report_dict['captial']:,.2f}")
        self.output(f"结束资金：\t{report_dict['end_balance']:,.2f}")

        self.output(f"总收益率：\t{report_dict['total_return']:,.2f}%")
        self.output(f"年化收益：\t{report_dict['annual_return']:,.2f}%")
        self.output(f"最大回撤：\t{report_dict['max_drawdown']:,.2f}")
        self.output(f"百分比最大回撤：{report_dict['max_ddpercent']:,.2f}%")

        self.output(f"总盈亏：\t{report_dict['total_net_pnl']:,.2f}")
        self.output(f"总手续费：\t{report_dict['total_commission']:,.2f}")
        self.output(f"总滑点：\t{report_dict['total_slippage']:,.2f}")
        self.output(f"总成交金额：\t{report_dict['total_turnover']:,.2f}")
        self.output(f"总成交笔数：\t{report_dict['total_trade_count']}")

        self.output(f"盈利个股数量：\t{report_dict['win_num']:,.2f}")
        self.output(f"亏损个股数量：\t{report_dict['loss_num']:,.2f}")
        self.output(f"胜率：\t{report_dict['win_rate']:,.2f}%")

        self.output(f"平均收益：\t{report_dict['daily_return']:,.2f}")
        self.output(f"收益标准差：\t{report_dict['return_std']:,.2f}%")
        self.output(f"Sharpe Ratio：\t{report_dict['sharpe_ratio']:,.2f}")

    @staticmethod
    def output(msg):
        print(f"{datetime.now()}\t{msg}")


if __name__ == "__main__":
    pt = PaperTrading()
    result, data = pt.creat("测试用账号")
    print(result)
    print(data)

