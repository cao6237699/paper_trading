
import json
from flask import Blueprint, request, jsonify

from paper_trading.trade.account import (
    order_generate,
    cancel_order_generate,
    liq_order_generate,
    on_account_add,
    on_account_exist,
    on_account_delete,
    query_account_list,
    query_account_one,
    query_position,
    query_orders,
    query_orders_today,
    on_orders_arrived,
    query_order_status,
    on_liquidation
)

# 主引擎
main_engine = None

# 数据库实例
db = None

blue = Blueprint('main_blue', __name__)

def init_blue(app, engine):
    """初始化蓝图"""
    app.register_blueprint(blue)

    # 绑定主引擎
    global main_engine, db
    main_engine = engine
    db = main_engine.db


@blue.route('/')
def index():
    return "欢迎使用模拟交易系统, 请参考README.MD 查阅相关文档"

@blue.route('/creat', methods=["POST"])
def account_creat():
    """创建账户"""
    rps = {}
    rps['status'] = True

    if request.form.get("info"):
        info = request.form["info"]
        token = on_account_add(info, db)
        if token:
            rps['data'] = token
        else:
            rps['status'] = False
            rps['data'] = "创建账户失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/delete', methods=["POST"])
def account_delete():
    """账户删除"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        result = on_account_delete(token, db)
        if result:
            rps['data'] = "账户删除成功"
        else:
            rps['status'] = False
            rps['data'] = "删除账户失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/list', methods=["GET"])
def account_list():
    """获取账户列表"""
    rps = {}
    rps['status'] = True

    account_list = query_account_list(db)

    if account_list:
        rps['data'] = account_list
    else:
        rps['status'] = False
        rps['data'] = "账户列表为空"

    return jsonify(rps)


@blue.route('/account', methods=["POST"])
def account_query():
    """查询账户信息"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        account = query_account_one(token, db)
        if account:
            rps['data'] = account
        else:
            rps['status'] = False
            rps['data'] = "查询账户失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/pos', methods=["POST"])
def position_query():
    """查询持仓信息"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        pos = query_position(token, db)
        if pos:
            rps['data'] = pos
        else:
            rps['status'] = False
            rps['data'] = "查询持仓失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/orders', methods=["POST"])
def orders_query():
    """查询交割单"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        orders = query_orders(token, db)
        if orders:
            rps['data'] = orders
        else:
            rps['status'] = False
            rps['data'] = "查询交割单失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/orders_today', methods=["POST"])
def orders_today_query():
    """查询交割单"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        orders = query_orders_today(token, db)
        if orders:
            rps['data'] = orders
        else:
            rps['status'] = False
            rps['data'] = "查询交割单失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/send', methods=["POST"])
def order_arrived():
    """接收订单"""
    rps = {}
    rps['status'] = True

    if request.form.get("order"):
        data = request.form["order"]
        data = json.loads(data)
        order = order_generate(data)
        if order:
            # 将订单送入数据库
            result, msg = on_orders_arrived(order, db)
            if result:
                # 将订单送入交易引擎
                main_engine.order_put(msg)
                rps['data'] = msg.order_id
            else:
                rps['status'] = False
                rps['data'] = msg
        else:
            rps['status'] = False
            rps['data'] = "订单数据错误"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/cancel', methods=["POST"])
def order_cancel():
    """取消订单"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        if request.form.get("order_id"):
            token = request.form["token"]
            order_id = request.form["order_id"]
            order = cancel_order_generate(token, order_id)
            if main_engine.order_put(order):
                rps['data'] = "撤单成功"
            else:
                rps['status'] = False
                rps['data'] = "撤单失败"
        else:
            rps['status'] = False
            rps['data'] = "请求参数错误"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/status', methods=["POST"])
def get_status():
    """查询订单状态"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        if request.form.get("order_id"):
            token = request.form["token"]
            order_id = request.form["order_id"]
            result, order_status = query_order_status(
                token, order_id, db)
            if result:
                rps['data'] = order_status
            else:
                rps['status'] = False
                rps['data'] = order_status
        else:
            rps['status'] = False
            rps['data'] = "请求参数错误"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/liquidation', methods=["POST"])
def liquidation():
    """查询订单状态"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        report_date = request.form["check_date"]
        price_dict = {}
        if request.form.get("price_dict"):
            price_dict = request.form["price_dict"]
            price_dict = json.loads(price_dict)
            if isinstance(price_dict, dict):
                for symbol, price in price_dict.items():
                    liq_order = liq_order_generate(token, symbol, price, report_date)
                    main_engine.order_put(liq_order)
                rps['data'] = "清算完成"
            else:
                rps['status'] = False
                rps['data'] = "请求参数错误"
                return jsonify(rps)
        else:
            rps['status'] = False
            rps['data'] = "请求参数错误"
            return jsonify(rps)
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/report', methods=['POST'])
def trade_report():
    """获取交易报告"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        start = request.form["start"]
        end = request.form["end"]
        statistics = main_engine.get_report(token, start, end)
        if isinstance(statistics, dict):
            rps['data'] = statistics
        else:
            rps['status'] = False
            rps['data'] = statistics
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)