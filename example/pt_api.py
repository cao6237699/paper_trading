
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 超时时间
MARKET_TIMEOUT = 3

class PaperTrading():
    """模拟交易"""

    def __init__(self, url: str = "", port: str = "", token: str = None, info: str = ""):
        """构造函数"""
        if url and port:
            self.home = ':'.join([url, port])
        else:
            raise ConnectionError("地址或者端口不能为空")

        # 连接模拟交易所
        result, msg = self.connect()

        if not result:
            self.connected = False
            raise ConnectionError(msg)

        if token:
            self._token = token
        else:
            status, new_token = self.creat(info)
            if status:
                self._token = new_token
                self.connected = True
            else:
                raise ValueError(new_token)

    def get_token(self):
        """获取token"""
        return self._token

    def get_url(self, method_name:str):
        """生成url"""
        return "/".join([self.home, method_name])

    def connect(self):
        """连接模拟交易程序"""
        url = self.get_url("")
        r = requests.get(url, timeout=MARKET_TIMEOUT)
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
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
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
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def get_list(self):
        """查询账户列表"""
        url = self.get_url("list")
        r = requests.get(url, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def account(self):
        """查询账户信息"""
        url = self.get_url("account")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def pos(self):
        """查询持仓信息"""
        url = self.get_url("pos")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def orders(self):
        """查询交割单信息"""
        url = self.get_url("orders")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def orders_today(self):
        """查询交割单信息"""
        url = self.get_url("orders_today")
        data = {'token': self._token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def order_send(self, order):
        """发单"""
        if isinstance(order, dict):
            order = json.dumps(order)
            order.encode("utf-8")
        url = self.get_url("send")
        data = {"order": order}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def order_cancel(self, order_id):
        """撤单"""
        url = self.get_url("cancel")
        data = {'token': self._token, "order_id": order_id}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def order_status(self, order_id):
        """查询订单状态"""
        url = self.get_url("status")
        data = {'token': self._token, "order_id": order_id}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def liquidation(self, check_date: str, price_dict: dict):
        """清算"""
        price_dict_data = json.dumps(price_dict)
        url = self.get_url("liquidation")
        data = {'token': self._token, 'check_date': check_date, "price_dict": price_dict_data.encode("utf-8")}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def report(self, start: str, end: str):
        """查询报告"""
        url = self.get_url("report")
        data = {'token': self._token, 'start': start, 'end': end}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def account_record(self, start: str,end: str):
        """查询账户逐日记录数据"""
        url = self.get_url("account_line")
        data = {'token': self._token, 'start': start, 'end': end}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def pos_record(self, start: str, end: str):
        """查询账户逐日记录数据"""
        url = self.get_url("pos_record")
        data = {'token': self._token, 'start': start, 'end': end}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
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
        self.output(f"最大回撤：{report_dict['max_ddpercent']:,.2f}%")

        self.output(f"总盈亏  ：\t{report_dict['total_net_pnl']:,.2f}")
        self.output(f"总手续费：\t{report_dict['total_commission']:,.2f}")
        self.output(f"总滑点  ：\t{report_dict['total_slippage']:,.2f}")
        self.output(f"总成交金额：\t{report_dict['total_turnover']:,.2f}")
        self.output(f"总成交笔数：\t{report_dict['total_trade_count']}")

        self.output(f"盈利个股数量：\t{report_dict['win_num']:,.2f}")
        self.output(f"亏损个股数量：\t{report_dict['loss_num']:,.2f}")
        self.output(f"胜率  ：\t{report_dict['win_rate']:,.2f}%")

        self.output(f"平均收益：\t{report_dict['daily_return']:,.2f}")
        self.output(f"收益标准差：\t{report_dict['return_std']:,.2f}%")
        self.output(f"Sharpe Ratio：\t{report_dict['sharpe_ratio']:,.2f}")

    def show_account_line(self, account_record: list):
        """显示资产曲线"""
        assets_df = pd.DataFrame(account_record)
        assets_df.sort_values(by='check_date', ascending=True, inplace=True)
        assets_df.index = assets_df['check_date']

        # 显示资产曲线
        plt.figure(figsize=(15, 5))
        plt.title("总资产曲线")
        plt.xlabel("日期")
        plt.ylabel("总资产(元)")
        plt.plot(assets_df['assets'])
        plt.show()

        # 显示持仓曲线

    def show_pos_record(self, pos_record: list):
        """显示持仓情况"""
        pos_df = pd.DataFrame(pos_record)
        pos_df.sort_values(by=['first_buy_date'], ascending=True, inplace=True)
        for i, row in pos_df.iterrows():
            print("代码：{}, 首次买入：{}, 最后卖出：{}, 累计买入：{}, 买均价：{}, 卖均价：{}, 盈亏：{}".format(
                row['pt_symbol'],
                row['first_buy_date'],
                row['last_sell_date'],
                row['max_vol'],
                row['buy_price_mean'],
                row['sell_price_mean'],
                row['profit']
            ))

    def show_orders(self, order_list: list):
        """显示订单"""
        order_df = pd.DataFrame(order_list)
        order_df.sort_values(by=['order_id'], ascending=True, inplace=True)
        for i, row in order_df.iterrows():
            print("日期：{}, 时间：{}, 类型：{}, 委托价格：{},成交价格：{}, 成交数量：{}".format(
                row['order_date'],
                row['order_time'],
                row['order_type'],
                row['order_price'],
                row['trade_price'],
                row['volume']
            ))

    def show_pos(self, pos_list: list):
        """显示持仓情况"""
        pos_df = pd.DataFrame(pos_list)
        pos_df.sort_values(by=['profit'], ascending=False, inplace=True)
        for i, row in pos_df.iterrows():
            print("证券代码：{}, 买入日期：{}, 总持仓：{}, 可用持仓：{}, 买入均价：{}, 当前价格：{}, 盈亏金额：{}".format(
                row['pt_symbol'],
                row['buy_date'],
                row['volume'],
                row['available'],
                row['buy_price'],
                row['now_price'],
                row['profit']
            ))

    @staticmethod
    def output(msg):
        print(f"{datetime.now()}\t{msg}")


if __name__ == "__main__":
    pt = PaperTrading()
    result, data = pt.creat("测试用账号")
    print(result)
    print(data)

