
import json
import requests
from datetime import datetime

import talib
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
from matplotlib.pylab import date2num
from matplotlib.dates import AutoDateLocator, DateFormatter


# 超时时间
MARKET_TIMEOUT = 120


class PaperTrading():
    """模拟交易"""

    def __init__(self, url: str = "", port: str = "", token: str = None, info: dict = None):
        """构造函数"""
        if url and port:
            self.home = ':'.join([url, port])
        else:
            raise ConnectionError("地址或者端口不能为空")

        # 连接模拟市场
        result, msg = self.connect()
        if not result:
            raise ConnectionError(msg)

        if token:
            # 账户登录
            status, account = self.login(token)
            if status:
                # 账户绑定
                self.account_bind(account)
            else:
                raise ValueError("账户不存在")
        else:
            # 账户创建并登录
            status, account = self.creat(info)
            if status:
                # 账户绑定
                self.account_bind(account)
            else:
                raise ValueError(account)

    @property
    def token(self):
        """获取token"""
        return self.__token

    @property
    def captial(self):
        """获取账户起始资本"""
        return self.__capital

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

    def account_bind(self, account):
        """账户绑定"""
        if isinstance(account, dict):
            self.__token = account['account_id']
            self.__capital = account['capital']
            self.__cost = account['cost']
            self.__tax = account['tax']
            self.__slippoint = account['slippoint']
        else:
            raise ValueError(account)

    @url_request
    def login(self, token: str):
        """
        登录账户
        :return:(status, data)  正确时数据类型(bool, dict) 错误时数据类型(bool, str)
        """
        url = self.get_url("login")
        data = {'token': token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def creat(self, info: dict):
        """
        创建模拟交易账户
        :param info:账户信息，可以在此定制账户参数，例如cost、sex等
        :return:(status, data)  正确时数据类型(bool, dict) 错误时数据类型(bool, str)
        """
        url = self.get_url("creat")
        if not isinstance(info, dict):
            raise ValueError("账户信息格式错误")

        info = json.dumps(info)
        info.encode("utf-8")
        data = {'info': info}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)

        return r

    @url_request
    def delete(self):
        """
        删除模拟交易账户
        :return:(status, data)  正确时数据类型(bool, str) 错误时数据类型(bool, str)
        """
        url = self.get_url("delete")
        data = {'token': self.__token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def get_list(self):
        """
        查询账户列表
        :return:(status, data)  正确时数据类型(bool, list) 错误时数据类型(bool, str)
        """
        url = self.get_url("list")
        r = requests.get(url, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def account(self):
        """
        查询账户信息
        :return:(status, data)  正确时数据类型(bool, dict) 错误时数据类型(bool, str)
        """
        url = self.get_url("account")
        data = {'token': self.__token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def pos(self):
        """
        查询持仓信息
        :return:(status, data)  正确时数据类型(bool, list) 错误时数据类型(bool, str)
        """
        url = self.get_url("pos")
        data = {'token': self.__token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def orders(self):
        """
        查询交割单信息
        :return:(status, data)  正确时数据类型(bool, list) 错误时数据类型(bool, str)
        """
        url = self.get_url("orders")
        data = {'token': self.__token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def orders_today(self):
        """
        查询交割单信息
        :return:(status, data)  正确时数据类型(bool, list) 错误时数据类型(bool, str)
        """
        url = self.get_url("orders_today")
        data = {'token': self.__token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def order_send(self, order):
        """
        发单
        :param order:dict格式订单数据
        :return:(status, data)  正确时数据类型(bool, str) 错误时数据类型(bool, str)
        """
        if isinstance(order, dict):
            order = json.dumps(order)
            order.encode("utf-8")
        url = self.get_url("send")
        data = {"order": order}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def order_cancel(self, order_id):
        """
        撤单
        :param order_id:订单ID
        :return:(status, data)  正确时数据类型(bool, str) 错误时数据类型(bool, str)
        """
        url = self.get_url("cancel")
        data = {'token': self.__token, "order_id": order_id}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def order_status(self, order_id):
        """
        查询订单状态
        :param order_id:订单ID
        :return:(status, data)  正确时数据类型(bool, str) 错误时数据类型(bool, str)
        """
        url = self.get_url("status")
        data = {'token': self.__token, "order_id": order_id}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def liquidation(self, check_date: str, price_dict: dict):
        """
        清算
        :param check_date:清算日期
        :param price_dict:清算时持仓清算价格
        :return:(status, data)  正确时数据类型(bool, str) 错误时数据类型(bool, str)
        """
        price_dict_data = json.dumps(price_dict)
        url = self.get_url("liquidation")
        data = {'token': self.__token, 'check_date': check_date, "price_dict": price_dict_data.encode("utf-8")}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def data_persistance(self):
        """
        数据持久化
        :return:
        """
        url = self.get_url("persistance")
        data = {'token': self.__token}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def replenish_captial(self):
        """补充资本"""
        pass

    @url_request
    def return_captial(self):
        """归还资本"""
        pass

    @url_request
    def account_record(self, start: str, end: str):
        """
        查询账户逐日记录数据
        :param start:数据开始日期
        :param end:数据结束日期
        :return:(status, data)  正确时数据类型(bool, list) 错误时数据类型(bool, str)
        """
        url = self.get_url("account_record")
        data = {'token': self.__token, 'start': start, 'end': end}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    @url_request
    def pos_record(self, start: str, end: str):
        """
        查询持仓记录数据
        :param start:数据开始日期
        :param end:数据结束日期
        :return:(status, data)  正确时数据类型(bool, list) 错误时数据类型(bool, str)
        """
        url = self.get_url("pos_record")
        data = {'token': self.__token, 'start': start, 'end': end}
        r = requests.post(url, data, timeout=MARKET_TIMEOUT)
        return r

    def get_assets_record(self, start, end, save_data=False):
        """
        获取逐日资产记录
        :param start:
        :param end:
        :param save_data:
        :return:dataframe数据
        """

        status, assets_record = self.account_record(start, end)
        if status:
            if isinstance(assets_record, list):
                assets_df = pd.DataFrame(assets_record)
                # 计算net_pnl收益情况
                assets_df['net_pnl'] = assets_df['assets'] - self.__capital
                assets_df = assets_df[['check_date', 'assets', 'available', 'market_value', 'net_pnl', 'account_id']]
                if save_data:
                    self.downloader(assets_df, start, end, "account.xls")

                return assets_df
            else:
                raise ValueError(assets_record)
        else:
            raise ValueError(assets_record)

    def get_pos_record(self, start, end, save_data=False):
        """
        获取逐日持仓记录
        :param start:
        :param end:
        :param save_data:
        :return:
        """
        status, pos_record = self.pos_record(start, end)
        if status:
            if isinstance(pos_record, list):
                pos_df = pd.DataFrame(pos_record)
                pos_df = pos_df[['pt_symbol', 'max_vol', 'first_buy_date','last_sell_date', 'buy_price_mean', 'sell_price_mean', 'profit', 'is_clear', 'account_id']]
                if save_data:
                    self.downloader(pos_df, start, end, "pos.xls")

                return pos_df
            else:
                raise ValueError(pos_record)
        else:
            raise ValueError(pos_record)

    def get_trade_record(self, start, end, save_data=False):
        """
        获取交易记录
        :param start:
        :param end:
        :param save_data:
        :return:
        """
        status, trade_record = self.orders()
        if status:
            if isinstance(trade_record, list):
                trade_df = pd.DataFrame(trade_record)
                trade_df = trade_df[trade_df['status'] == "全部成交"]
                trade_df['commission'] = 0.

                # 计算commission
                for i, row in trade_df.iterrows():
                    commission = 0.
                    if row['order_type'] == "buy":
                        commission = row['traded'] * row['trade_price'] * self.__cost
                    elif row['order_type'] == "sell":
                        commission = row['traded'] * row['trade_price'] * (self.__cost + self.__tax)
                    else:
                        pass

                    trade_df.loc[i, 'commission'] = commission

                trade_df = trade_df[['order_date', 'order_time', 'pt_symbol', 'order_type', 'price_type', 'order_price', 'trade_price', 'volume', 'traded', 'status', 'commission', 'status', 'trade_type','account_id', 'error_msg']]
                if save_data:
                    self.downloader(trade_df, start, end, "orders.xls")

                return trade_df
            else:
                raise ValueError(trade_record)
        else:
            raise ValueError(trade_record)

    def data_statistics(self, assets_df, pos_df, trade_df, save_data=False):
        """交易结果分析"""
        # 初始资金
        start_date = assets_df.iloc[0]['check_date']
        end_date = assets_df.iloc[-1]['check_date']

        total_days = len(assets_df)
        profit_days = len(assets_df[assets_df["net_pnl"] > 0])
        loss_days = len(assets_df[assets_df["net_pnl"] < 0])

        end_balance = float(assets_df.iloc[-1].assets)

        max_drawdown = self.max_drapdown_cal(assets_df)
        max_ddpercent = round((max_drawdown / assets_df['assets'].max()) * 100, 2)

        total_net_pnl = round((end_balance - self.__capital), 2)
        total_commission = float(trade_df['commission'].sum())
        total_slippage = 0
        total_turnover = float(trade_df['volume'].sum())
        total_trade_count = len(trade_df)

        win_num = len(pos_df[pos_df.profit > 0])
        loss_num = len(pos_df[pos_df.profit <= 0])
        win_rate = round((win_num / (win_num + loss_num) * 100), 2)

        total_return = round(((end_balance / self.__capital - 1) * 100), 2)
        annual_return = round((total_return / total_days * 240), 2)
        return_mean = pos_df['profit'].mean()
        return_std = pos_df['profit'].std()

        if return_std:
            sharpe_ratio = float(return_mean / return_std * np.sqrt(240))
        else:
            sharpe_ratio = 0

        statistics = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "captial": self.__capital,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "total_net_pnl": total_net_pnl,
            "total_commission": total_commission,
            "total_slippage": total_slippage,
            "total_turnover": total_turnover,
            "total_trade_count": total_trade_count,
            "win_num": win_num,
            "loss_num": loss_num,
            "win_rate": win_rate,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": return_mean,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
        }

        if save_data:
            self.downloader(statistics, start_date, end_date, "report.xls")

        return statistics

    def get_report(self, start: str, end: str):
        """获取交易报告"""
        trade_df = self.get_trade_record(start, end)

        if not len(trade_df):
            print("成交记录为空，无法计算")
            return {}

        # 展示账户曲线
        assets_df = self.get_assets_record(start, end)

        # 展示持仓记录
        pos_df = self.get_pos_record(start, end)

        # 计算分析结果
        statistics_result = self.data_statistics(assets_df, pos_df, trade_df)

        return statistics_result

    def show_report(self, start: str, end: str, save_data=False):
        """显示分析报告"""
        trade_df = self.get_trade_record(start, end, save_data)

        if not len(trade_df):
            return False, "成交记录为空，无法计算"

        # 展示账户曲线
        assets_df = self.get_assets_record(start, end, save_data)
        self.show_account_line(assets_df)

        # 展示持仓记录
        pos_df = self.get_pos_record(start, end, save_data)

        # 计算分析结果
        statistics_result = self.data_statistics(assets_df, pos_df, trade_df)

        # 展示分析结果
        self.show_statistics(statistics_result)

    def show_statistics(self, report_dict: dict):
        """显示报告"""
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
        self.output(f"百分比最大回撤：\t{report_dict['max_ddpercent']:,.2f}%")

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

    def show_account_line(self, assets_df):
        """显示资产曲线"""
        assets_df.sort_values(by='check_date', ascending=True, inplace=True)
        assets_df.index = assets_df['check_date']

        plt.rcParams['font.sans-serif'] = ['SimHei']

        plt.figure(figsize=(16, 5))
        plt.title("总资产曲线")
        plt.xlabel("交易日期")
        plt.ylabel("资产")
        plt.plot(assets_df['assets'])
        plt.show()

        # 显示持仓曲线

    def show_pos_record(self, pos_df):
        """显示持仓情况"""
        pos_df.sort_values(by=['first_buy_date'], ascending=True, inplace=True)
        pos_df = pos_df[['pt_symbol', 'first_buy_date', 'last_sell_date', 'max_vol', 'buy_price_mean', 'sell_price_mean', 'profit']]
        pos_df.columns = ['代码', '首次买入', '最后卖出', '累计买入', '买均价', '卖均价', '盈亏']
        print(pos_df)

    def show_orders_record(self, order_df):
        """显示订单记录"""
        order_df.sort_values(by=['order_id'], ascending=True, inplace=True)
        order_df = order_df[
            ['order_date', 'order_time', 'order_type', 'order_price', 'trade_price', 'volume']]
        order_df.columns = ['日期', '时间', '类型', '委托价格', '成交价格', '成交数量']
        print(order_df)

    def show_order_kline(self, kline_data, order_df):
        """显示K线并标记买入卖出点"""
        # TODO 暂时不能通用只能识别pytdx 的get_k_data函数功能
        # 设置mpl样式
        mpl.style.use('ggplot')

        #转换kline_data index类型
        kline_data.date = pd.to_datetime(kline_data.date)
        kline_data.index = kline_data.date

        # 加载策略使用的指标,最多支持三条均线
        kline_data['ma3'] = talib.SMA(kline_data.close, 3)
        kline_data['ma5'] = talib.SMA(kline_data.close, 5)
        kline_data['ma14'] = talib.SMA(kline_data.close, 14)

        # 绘制第一个图
        fig = plt.figure()
        fig.set_size_inches((16, 16))

        ax_canddle = fig.add_axes((0, 0.7, 1, 0.3))
        ax_vol = fig.add_axes((0, 0.45, 1, 0.2))

        data_list = list()
        for date, row in kline_data[['open', 'high', 'low', 'close']].iterrows():
            t = date2num(date)
            open ,high, low, close = row[:]
            d = (t, open, high, low, close)
            data_list.append(d)

        # 绘制蜡烛图
        candlestick_ohlc(ax_canddle, data_list, colorup='r', colordown='green', alpha=0.7, width=0.8)

        # 将x轴设置为时间类型
        ax_canddle.xaxis_date()

        ax_canddle.plot(kline_data.index, kline_data['ma3'], label="ma3")
        ax_canddle.plot(kline_data.index, kline_data['ma5'], label="ma5")
        ax_canddle.plot(kline_data.index, kline_data['ma14'], label="ma14")
        ax_canddle.legend()

        # 绘制VOL
        ax_vol.bar(kline_data.index, kline_data.volume/1000000)
        ax_vol.set_ylabel("millon")
        ax_vol.set_xlabel("date")

        # 标记订单点位
        order_df.order_date = pd.to_datetime(order_df.order_date)
        for i, row in order_df.iterrows():
            if row['status'] == "全部成交":
                order_date = row['order_date']
                if row['order_type'] == "buy":
                    ax_canddle.annotate("B",
                                        xy=(order_date, kline_data.loc[order_date].low),
                                        xytext=(order_date, kline_data.loc[order_date].low - 1),
                                        arrowprops=dict(facecolor="r",
                                                        alpha=0.3,
                                                        headlength=10,
                                                        width=10))
                else:
                    ax_canddle.annotate("S",
                                        xy=(order_date, kline_data.loc[order_date].high),
                                        xytext=(order_date, kline_data.loc[order_date].high + 1),
                                        arrowprops=dict(facecolor="g",
                                                        alpha=0.3,
                                                        headlength=10,
                                                        width=10))

    def show_pos(self, pos_list: list):
        """显示持仓情况"""
        if pos_list:
            pos_df = pd.DataFrame(pos_list)
            pos_df.sort_values(by=['profit'], ascending=False, inplace=True)
            pos_df = pos_df[
                ['pt_symbol', 'buy_date', 'volume', 'available', 'buy_price', 'now_price',
                 'profit']]
            pos_df.columns = ['证券代码', '买入日期', '总持仓', '可用持仓', '买入均价', '当前价格', '盈亏金额']
            print(pos_df)
        else:
            print("无持仓")

    def downloader(self, data, start_date, end_date, file_name):
        """测试结果下载"""
        # 获取地址
        file_name = "_".join([start_date, end_date, file_name])
        file_path = self.get_folder_path(file_name)

        if isinstance(data, dict):
            data_list = list()
            data_list.append(data)
            df = pd.DataFrame(data_list)
        else:
            df = pd.DataFrame(data)

        df.to_excel(file_path)
        print(f"数据已保存，地址为：{file_path}")

    def get_folder_path(self, file_name):
        """获取文件夹路径"""
        save_addr = Path.cwd()
        folder_path = save_addr.joinpath(self.__token)

        if not folder_path.exists():
            folder_path.mkdir()

        return folder_path.joinpath(file_name)

    def max_drapdown_cal(self, assets_df):
        """最大回撤计算"""
        drawdown_list = list()
        assets_list = list()
        base_data = 0
        for i, row in assets_df.iterrows():
            # 资产增长
            if base_data <= row['assets']:
                if assets_list:
                    assets_list.append(base_data)
                    assets_list.sort()
                    assets_diff = assets_list[-1] - assets_list[0]
                    drawdown_list.append(assets_diff)
                    assets_list.clear()
                base_data = row['assets']
            # 资产减少
            else:
                assets_list.append(row['assets'])

        if drawdown_list:
            drawdown_list.sort()
            return drawdown_list[-1]
        else:
            return 0

    @staticmethod
    def output(msg):
        print(f"{datetime.now()}\t{msg}")


if __name__ == "__main__":
    pass

