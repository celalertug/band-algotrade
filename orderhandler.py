import assetmanager as asm
from coinex import borsa_instance as b
from log import logprint


def buy_order(symbol):
    # symbol = "ETHUSDT"
    if not asm.is_in_open_position(symbol) and asm.is_left_free_pos():
        pos_base_amount = asm.get_pos_base_amount()
        ret = b.buy(symbol, pos_base_amount)
        print(ret)
        logprint("buy", ret)
        if ret["status"] == "done":
            avg_price = float(ret.get("avg_price", 0))
            amount = asm.get_one_balance_from_exchange(symbol=symbol)
            asm.add_trade_history(symbol, "buy", amount, avg_price)
            asm.add_open_position(symbol, amount)
            asm.update_free_base_balance()


def sell_order(symbol):
    # symbol = "ETHUSDT"
    if asm.is_in_open_position(symbol=symbol):
        amount = asm.get_one_balance_from_open_positions(symbol)
        ret = b.sell(symbol, amount)
        logprint("sell", ret)
        print(ret)
        if ret["status"] == "done":
            avg_price = float(ret.get("avg_price", 0))
            asm.add_trade_history(symbol, "sell", amount, avg_price)
            asm.remove_from_open_positions(symbol)
            asm.update_free_base_balance()


if __name__ == '__main__' and 1:  # buy & sell
    pass
    print("start buying")
    buy_order(symbol="ETHUSDT")
    print("start selling")
    sell_order(symbol="ETHUSDT")

