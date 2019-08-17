
import json
import requests

SETTINGS = {
    "URL": "http://127.0.0.1",
    "PORT": "5000",
    "TIMEOUT": 3
}

class PaperTrading():
    """模拟交易"""

    def __init__(self, token: str = None):
        self.home = ':'.join([SETTINGS["URL"], SETTINGS["PORT"]])
        self._token = token

    def get_url(self, method_name:str):
        """生成url"""
        return "/".join([self.home, method_name])

    def connect(self):
        """连接模拟交易程序"""
        url = self.get_url("")
        r = requests.get(url, timeout=SETTINGS["TIMEOUT"])
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
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
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
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
        return r

    @url_request
    def get_list(self):
        """查询账户列表"""
        url = self.get_url("list")
        r = requests.get(url, timeout=SETTINGS["TIMEOUT"])
        return r

    @url_request
    def account(self):
        """查询账户信息"""
        url = self.get_url("account")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
        return r

    @url_request
    def pos(self):
        """查询持仓信息"""
        url = self.get_url("pos")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
        return r

    @url_request
    def orders(self):
        """查询交割单信息"""
        url = self.get_url("orders")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
        return r

    @url_request
    def order_send(self, order):
        """发单"""
        if isinstance(order, dict):
            order = json.dumps(order)
            order.encode("utf-8")
        url = self.get_url("send")
        data = {"order": order}
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
        return r

    @url_request
    def order_cancel(self, order_id):
        """撤单"""
        url = self.get_url("cancel")
        data = {'token': self._token, "order_id": order_id}
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
        return r

    @url_request
    def order_status(self, order_id):
        """查询订单状态"""
        url = self.get_url("status")
        data = {'token': self._token, "order_id": order_id}
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
        return r

    @url_request
    def liquidation(self, price_dict):
        """清算"""
        url = self.get_url("liquidation")
        data = {'token': self._token, "price_dict": price_dict}
        r = requests.post(url, data, timeout=SETTINGS["TIMEOUT"])
        return r


if __name__ == "__main__":
    pt = PaperTrading()
    result, data = pt.creat("测试用账号")
    print(result)
    print(data)

