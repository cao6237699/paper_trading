
import json
from datetime import timedelta
from flask import Flask, g, request, jsonify

from paper_trading.api.db import MongoDBService
from paper_trading.trade.account import (
    order_generate,
    on_account_add,
    on_account_exist,
    on_account_delete,
    query_account_list,
    query_account_one,
    query_position,
    query_orders,
    on_orders_arrived,
    on_orders_book_cancel,
    query_order_status,
    on_liquidation
)


__all__ = ['app']

app = Flask(__name__)

app.config['SECRET_KEY'] = "j1as78a1gf6a4ea1f5d6a78e41fa56e"
# 设置session的保存时间。
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)


def get_db():
    """获取数据库连接"""
    if not hasattr(g, 'db_client'):
        g.db_client = MongoDBService()
        g.db_client.connect_db()
    return g.db_client


@app.route('/')
def index():
    return "欢迎使用模拟交易系统, 请参考README.MD 查阅相关文档"


@app.route('/creat', methods=["POST"])
def account_creat():
    """创建账户"""
    rps = {}
    rps['status'] = True

    if request.form.get("info"):
        info = request.form["info"]
        db_client = get_db()
        token = on_account_add(info, db_client)
        if token:
            rps['data'] = token
        else:
            rps['status'] = False
            rps['data'] = "创建账户失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@app.route('/delete', methods=["POST"])
def account_delete():
    """账户删除"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        db_client = get_db()
        result = on_account_delete(token, db_client)
        if result:
            rps['data'] = "账户删除成功"
        else:
            rps['status'] = False
            rps['data'] = "删除账户失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@app.route('/list', methods=["GET"])
def account_list():
    """获取账户列表"""
    rps = {}
    rps['status'] = True

    db_client = get_db()
    account_list = query_account_list(db_client)

    if account_list:
        rps['data'] = account_list
    else:
        rps['status'] = False
        rps['data'] = "账户列表为空"

    return jsonify(rps)


@app.route('/account', methods=["POST"])
def account_query():
    """查询账户信息"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        db_client = get_db()
        account = query_account_one(token, db_client)
        if account:
            rps['data'] = account
        else:
            rps['status'] = False
            rps['data'] = "查询账户失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@app.route('/pos', methods=["POST"])
def position_query():
    """查询持仓信息"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        db_client = get_db()
        pos = query_position(token, db_client)
        if pos:
            rps['data'] = pos
        else:
            rps['status'] = False
            rps['data'] = "查询持仓失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@app.route('/orders', methods=["POST"])
def orders_query():
    """查询交割单"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        db_client = get_db()
        orders = query_orders(token, db_client)
        if orders:
            rps['data'] = orders
        else:
            rps['status'] = False
            rps['data'] = "查询交割单失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@app.route('/send', methods=["POST"])
def order_arrived():
    """接收订单"""
    rps = {}
    rps['status'] = True

    if request.form.get("order"):
        data = request.form["order"]
        data = json.loads(data)
        order = order_generate(data)
        if order:

            db_client = get_db()
            result, msg = on_orders_arrived(order, db_client)
            if result:
                rps['data'] = msg
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


@app.route('/cancel', methods=["POST"])
def order_cancel():
    """取消订单"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        if request.form.get("order_id"):
            token = request.form["token"]
            order_id = request.form["order_id"]
            db_client = get_db()
            result = on_orders_book_cancel(token, order_id, db_client)
            if result:
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


@app.route('/status', methods=["POST"])
def get_status():
    """查询订单状态"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        if request.form.get("order_id"):
            token = request.form["token"]
            order_id = request.form["order_id"]
            db_client = get_db()
            result, order_status = query_order_status(
                token, order_id, db_client)
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


@app.route('/liquidation', methods=["POST"])
def liquidation():
    """查询订单状态"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        price_dict = {}
        if request.form.get("price_dict"):
            price_dict = request.form.get("price_dict")
            price_dict = json.loads(price_dict)
        else:
            if not request.form.get("price_dict") == []:
                rps['status'] = False
                rps['data'] = "请求参数错误"
                return jsonify(rps)

        db_client = get_db()
        if on_account_exist(token, db_client):
            result = on_liquidation(db_client, token, price_dict)
            if result:
                rps['data'] = "清算完成"
            else:
                rps['status'] = False
                rps['data'] = "清算失败"

        else:
            rps['status'] = False
            rps['data'] = "账户信息不存在"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)
