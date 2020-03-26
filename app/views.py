
import json
from flask import Blueprint, request, jsonify, render_template

from paper_trading.api.db import MongoDBService
from paper_trading.trade.data_center import (
    get_stock_daily_qfq,
    get_stock_mtime
)
from paper_trading.trade.account import (
    new_order_generate,
    cancel_order_generate,
    liq_order_generate,
    on_account_add,
    on_account_exist,
    on_account_delete,
    on_orders_arrived,
    query_account_list,
    query_account_one,
    query_account_record,
    query_position,
    query_position_record,
    query_orders,
    query_orders_today,
    query_orders_by_symbol,
    query_order_status
)

# 主引擎
main_engine = None

# 数据库实例
db = None
test_db = None

# 行情实例
tdx = None

blue = Blueprint('main_blue', __name__)

def init_blue(app, engine):
    """初始化蓝图"""
    app.register_blueprint(blue)

    # 绑定主引擎
    global main_engine, db, test_db, tdx
    main_engine = engine

    # 连接数据库，用于数据查询
    db = main_engine.creat_db()
    db.connect_db()

    # 连接行情源
    tdx = main_engine.creat_hq_api()

    # 连接测试行情数据库
    test_db = MongoDBService('192.168.1.251', 27017)
    test_db.connect_db()


@blue.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@blue.route('/creatPage', methods=['GET', 'POST'])
def my_account():
    return render_template("account.html")


@blue.route('/trade', methods=['GET', 'POST'])
def my_trade():
    return render_template("trade.html")


@blue.route('/train_k', methods=['GET'])
def my_train_k():
    return render_template("train_k.html")


@blue.route('/review', methods=['GET'])
def trade_review():
    """交易回看"""
    return render_template("review.html")


@blue.route('/creat', methods=["POST"])
def account_creat():
    """创建账户"""
    rps = {}
    rps['status'] = True

    if request.form.get("info"):
        info = request.form["info"]
        info_dict = json.loads(info)
        token = on_account_add(info_dict, db)
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
        if on_account_exist(token, db):
            result = on_account_delete(token, db)
            if result:
                rps['data'] = "账户删除成功"
            else:
                rps['status'] = False
                rps['data'] = "删除账户失败"
        else:
            rps['status'] = False
            rps['data'] = "账户不存在"
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
    """查询所有订单"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        orders = query_orders(token, db)
        if orders:
            rps['data'] = orders
        else:
            rps['status'] = False
            rps['data'] = "查询订单失败"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/orders_today', methods=["POST"])
def orders_today_query():
    """查询当日订单"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        orders = query_orders_today(token, db)
        if orders:
            rps['data'] = orders
        else:
            rps['status'] = False
            rps['data'] = "查询当日订单失败"
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
        order = new_order_generate(data)
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
    """清算"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        if on_account_exist(token, db):
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
            else:
                rps['status'] = False
                rps['data'] = "请求参数错误"
        else:
            rps['status'] = False
            rps['data'] = "账户不存在"
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
        if on_account_exist(token, db):
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
            rps['data'] = "账户不存在"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/account_line', methods=['POST'])
def get_account_record():
    """获取账户记录数据"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        start = request.form["start"]
        end = request.form["end"]
        account_record = query_account_record(token, db, start, end)
        if account_record:
            rps['data'] = account_record
        else:
            rps['status'] = False
            rps['data'] = "无数据"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/pos_record', methods=['POST'])
def get_pos_record():
    """获取持仓记录数据"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        start = request.form["start"]
        end = request.form["end"]
        pos_record = query_position_record(token, db, start, end)
        if pos_record:
            rps['data'] = pos_record
        else:
            rps['status'] = False
            rps['data'] = "无数据"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


"""for web page"""


@blue.route('/orders_page', methods=["POST"])
def orders_for_page():
    """页面查询所有订单"""
    rps = []
    if request.form.get("token"):
        token = request.form["token"]
        orders = query_orders(token, db)
        if orders:
            if isinstance(orders, list):
                rps = orders

    new_data = {'aaData': rps}
    return jsonify(new_data)


@blue.route('/orders_today_page', methods=["POST"])
def orders_today_for_page():
    """页面查询当日的订单"""
    rps = []
    if request.form.get("token"):
        token = request.form["token"]
        orders = query_orders_today(token, db)
        if orders:
            if isinstance(orders, list):
                rps = orders

    new_data = {'aaData':rps}
    return jsonify(new_data)


@blue.route('/orders_page_by_symbol', methods=["POST"])
def orders_for_page_by_symbol():
    """页面查询当日的订单"""
    rps = []
    if request.form.get("token"):
        token = request.form["token"]
        symbol = request.form["symbol"]
        orders = query_orders_by_symbol(token, symbol, db)
        if orders:
            if isinstance(orders, list):
                rps = orders

    new_data = {'aaData':rps}
    return jsonify(new_data)


@blue.route('/pos_record_page', methods=['POST'])
def get_pos_record_for_page():
    """获取持仓记录数据"""
    rps = []
    if request.form.get("token"):
        token = request.form["token"]
        pos = query_position_record(token, db)
        if pos:
            if isinstance(pos, list):
                rps = pos

    new_data = {'aaData': rps}
    return jsonify(new_data)


"""get stock data"""

@blue.route('/test_hq_page', methods=['POST'])
def get_test_hq_for_page():
    """获取测试用k线数据"""
    rps = {}
    rps['status'] = True

    if request.form.get("symbol") or request.form.get("start") or request.form.get("end"):
        symbol = request.form["symbol"]
        start = request.form["start"]
        end = request.form["end"]
        data = get_stock_daily_qfq(symbol, start, end, test_db)
        if data:
            rps['data'] = data
        else:
            rps['status'] = False
            rps['data'] = "无数据"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/kline_page', methods=['POST'])
def get_kline_for_page():
    """获取k线数据"""
    rps = []
    if request.form.get("token"):
        token = request.form["token"]
        pos = query_position_record(token, db)
        if pos:
            if isinstance(pos, list):
                rps = pos

    new_data = {'aaData': rps}
    return jsonify(new_data)


@blue.route('/mtime_page', methods=['POST'])
def get_mtime_for_page():
    """获取分时数据"""
    rps = {}
    rps['status'] = True

    if request.form.get("symbol") or request.form.get("timestamp"):
        symbol = request.form["symbol"]
        timestamp = request.form["timestamp"]
        data = get_stock_mtime(symbol, timestamp, tdx)
        if data:
            rps['data'] = data
        else:
            rps['status'] = False
            rps['data'] = "无数据"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)
