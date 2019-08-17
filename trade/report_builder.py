

def calculate_result(self):
    """计算结果"""
    self.write_log("开始计算逐日盯市盈亏")

    if not self.trades:
        self.write_log("成交记录为空，无法计算")
        return

    # 资产表
    self.assets_df = self.get_account_data()
    # 持仓表
    self.pos_df = self.get_pos_data()
    # 交易表
    self.trade_df = self.get_trade_data()
    self.write_log("逐日盯市盈亏计算完成")


def trade_statistics(self):
    """交易结果分析"""
    self.write_log("开始分析策略统计指标")

    if not self.trades:
        self.write_log("成交记录为空，无法计算")
        return

    start_date = self.trade_date[0]
    end_date = self.trade_date[-1]

    total_days = len(self.trade_date)
    profit_days = len(self.assets_df[self.assets_df["net_pnl"] > 0])
    loss_days = len(self.assets_df[self.assets_df["net_pnl"] < 0])

    end_balance = self.account_dict[self.trade_date[-1]].assets
    max_drawdown = self.assets_df['assets'].max() - self.assets_df['assets'].min()
    max_ddpercent = 0

    total_net_pnl = end_balance - self.capital
    total_commission = self.trade_df['commission'].sum()
    total_slippage = 0
    total_turnover = self.trade_df['turnover'].sum()
    total_trade_count = len(self.trade_df)

    win_num = len(self.pos_df[self.pos_df.pnl > 0])
    loss_num = len(self.pos_df[self.pos_df.pnl <= 0])
    win_rate = win_num / (win_num + loss_num) * 100

    total_return = (end_balance / self.capital - 1) * 100
    annual_return = total_return / total_days * 240
    return_mean = self.pos_df['pnl'].mean()
    return_std = self.pos_df['pnl'].std()

    if return_std:
        sharpe_ratio = return_mean / return_std * np.sqrt(240)
    else:
        sharpe_ratio = 0

    # Output
    self.output("-" * 30)
    self.output(f"首个交易日：\t{start_date}")
    self.output(f"最后交易日：\t{end_date}")

    self.output(f"总交易日：\t{total_days}")
    self.output(f"盈利交易日：\t{profit_days}")
    self.output(f"亏损交易日：\t{loss_days}")

    self.output(f"起始资金：\t{self.capital:,.2f}")
    self.output(f"结束资金：\t{end_balance:,.2f}")

    self.output(f"总收益率：\t{total_return:,.2f}%")
    self.output(f"年化收益：\t{annual_return:,.2f}%")
    self.output(f"最大回撤: \t{max_drawdown:,.2f}")
    self.output(f"百分比最大回撤: {max_ddpercent:,.2f}%")

    self.output(f"总盈亏：\t{total_net_pnl:,.2f}")
    self.output(f"总手续费：\t{total_commission:,.2f}")
    self.output(f"总滑点：\t{total_slippage:,.2f}")
    self.output(f"总成交金额：\t{total_turnover:,.2f}")
    self.output(f"总成交笔数：\t{total_trade_count}")

    self.output(f"盈利个股数量：\t{win_num:,.2f}")
    self.output(f"亏损个股数量：\t{loss_num:,.2f}")
    self.output(f"胜率：\t{win_rate:,.2f}%")

    self.output(f"平均收益率：\t{return_mean:,.2f}%")
    self.output(f"收益标准差：\t{return_std:,.2f}%")
    self.output(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")

    statistics = {
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "profit_days": profit_days,
        "loss_days": loss_days,
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


def trade_record(self):
    """交易记录"""
    for i, trade in self.trades.items():
        print("订单编号：{}, 成交编号：{}, 交易日期：{}, 交易时间：{}, 证券代码：{}, 订单类型：{}, 成交价格：{}, 成交数量：{}".format(
            trade.order_id,
            trade.trade_id,
            trade.check_date,
            trade.time,
            trade.lz_symbol,
            trade.order_type.value,
            trade.price,
            trade.volume
        ))


def trade_chart(self):
    """交易结果图标展示"""
    pass




