
import json
from flask import Blueprint, request, jsonify, render_template

from paper_trading.api.db import MongoDBService
from paper_trading.trade.data_center import (
    get_stock_daily_qfq,
    get_stock_mtime
)
from paper_trading.trade.account import (
    new_order_generate,
    cancel_order_generate
)
from paper_trading.trade.db_model import (
    on_account_exist,
    on_account_delete,
    query_account_list,
    query_orders_by_symbol,
    query_order_status,
    query_order_one, query_orders)

# 主引擎
main_engine = None

# 账户引擎
account_engine = None

# 数据库实例
db = None
test_db = None

# 行情实例
tdx = None

blue = Blueprint('main_blue', __name__)

def init_blue(app, engine):
    """初始化蓝图"""
    app.register_blueprint(blue)

    global main_engine, account_engine, db, test_db, tdx

    # 绑定主引擎和账户引擎
    main_engine = engine
    account_engine = engine.account_engine

    # 连接数据库，用于数据查询
    db = main_engine.creat_db()

    # 连接行情源
    tdx = main_engine.creat_hq_api()

    # 连接测试行情数据库
    test_db = MongoDBService('192.168.1.251', 27017)
    test_db.connect_db()


"""web page"""


@blue.route('/', methods=['GET', 'POST'])
def index():
    """主页"""
    return render_template("index.html")


@blue.route('/creatPage', methods=['GET', 'POST'])
def my_account():
    """创建账户页面"""
    return render_template("account.html")


@blue.route('/trade', methods=['GET', 'POST'])
def my_trade():
    """模拟交易页面"""
    return render_template("trade.html")


@blue.route('/train_k', methods=['GET'])
def my_train_k():
    """交易训练页面"""
    return render_template("train_k.html")


@blue.route('/review', methods=['GET'])
def trade_review():
    """交易回看"""
    return render_template("review.html")


"""trade api"""


@blue.route('/login', methods=["POST"])
def account_login():
    """账户登录"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        account = account_engine.login(token)
        if account:
            rps['data'] = account
        else:
            rps['status'] = False
            rps['data'] = "账户不存在"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/creat', methods=["POST"])
def account_creat():
    """创建账户"""
    rps = {}
    rps['status'] = True

    if request.form.get("info"):
        info = request.form["info"]
        info_dict = json.loads(info)
        account = account_engine.creat(info_dict)
        if account:
            rps['data'] = account
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
            account_engine.logout(token)
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
        status, account = account_engine.query_account_data(token)
        rps['status'] = status
        rps['data'] = account
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
        status, pos = account_engine.query_pos_data(token)
        rps['status'] = status
        rps['data'] = pos
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
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        if start_date and end_date:
            flt = {"order_date": {"$gte": start_date, "$lte": end_date}}
        else:
            flt = {}
        try:
            data = query_orders(token, db, flt)
        except Exception as e:
            status = False
            data = "查询订单失败"
        else:
            status = True
        rps['status'] = status
        rps['data'] = data
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
        status, orders = account_engine.query_orders_today(token)
        rps['status'] = status
        rps['data'] = orders
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
            result, msg = main_engine.on_orders_arrived(order)
            if result:
                # 将订单送入交易引擎
                main_engine.order_put(msg)
                rps['data'] = {"order_id": msg.order_id}
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
            result, order = query_order_one(
                token, order_id, db)
            if not result:
                rps['status'] = False
                rps['data'] = "查询订单失败"
            else:
                order = cancel_order_generate(token, order_id, code=order["code"], exchange=order["exchange"])
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
        liq_date = request.form["check_date"]
        price_dict = {}
        if request.form.get("price_dict"):
            price_dict = request.form["price_dict"]
            price_dict = json.loads(price_dict)
            if isinstance(price_dict, dict):
                if account_engine.liq_manual(token, liq_date, price_dict):
                    rps['data'] = "清算完成"
                else:
                    rps['status'] = False
                    rps['data'] = "清算失败"
            else:
                rps['status'] = False
                rps['data'] = "请求参数错误"
        else:
            rps['status'] = False
            rps['data'] = "请求参数错误"
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/account_record', methods=['POST'])
def get_account_record():
    """获取账户记录数据"""
    rps = {}
    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        start = request.form["start"]
        end = request.form["end"]
        status, account_record = account_engine.query_account_record(token, start, end)
        rps['status'] = status
        rps['data'] = account_record
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
        status, pos_record = account_engine.query_pos_record(token, start, end)
        rps['status'] = status
        rps['data'] = pos_record
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/persistance', methods=['POST'])
def persistance():
    """数据持久化"""
    rps = {}

    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        result = account_engine.data_persistance(token)
        if isinstance(result, bool):
            rps['data'] = "数据保存完毕"
        else:
            rps['status'] = False
            rps['data'] = result
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)


@blue.route('/test', methods=['POST'])
def test():
    """数据持久化"""
    rps = {}

    rps['status'] = True

    if request.form.get("token"):
        token = request.form["token"]
        main_engine.test()
        rps['data'] = ""
    else:
        rps['status'] = False
        rps['data'] = "请求参数错误"

    return jsonify(rps)

"""data for web page"""


@blue.route('/orders_page', methods=["POST"])
def orders_for_page():
    """页面查询所有订单"""
    rps = []
    if request.form.get("token"):
        token = request.form["token"]
        orders = account_engine.query_orders(token)
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
        status, orders = account_engine.query_orders_today(token)
        if orders:
            if isinstance(orders, list):
                rps = orders

    new_data = {'aaData':rps}
    return jsonify(new_data)


@blue.route('/orders_page_by_symbol', methods=["POST"])
def orders_for_page_by_symbol():
    """页面查询某只证券的订单"""
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
        pos_record = account_engine.query_pos_record(token)
        if pos_record:
            if isinstance(pos_record, list):
                rps = pos_record

    new_data = {'aaData': rps}
    return jsonify(new_data)


"""stock data"""

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
        pos = account_engine.query_account_data(token)
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
