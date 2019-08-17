
from paper_trading.app.server import app
from paper_trading.trade.pt_engine import MainEngine


def main():
    me = MainEngine()

    # 开启模拟交易引擎
    if me.start():
        # 开启flask服务, 如果要开启多个模拟交易程序，请记得更换端口
        app.run(host='127.0.0.1', port=5000, debug=False)


if __name__ == "__main__":
    main()




