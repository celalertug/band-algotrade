from datetime import datetime, timedelta
from coinex import borsa_instance as b
import json
from copy import deepcopy
from conf import getparam

# base_currency = "USDT"
base_currency = getparam("base_currency")

trade_history = []
# poslimit = 6
poslimit = getparam("poslimit")

free_base_balance = 0
open_positions = []

# write_down_trade_history = True
write_down_trade_history = getparam("write_down_trade_history")


# borsadan guncel base_currency miktarini ceker
def update_free_base_balance():
    global free_base_balance
    b.get_all_balance()
    ret = b.get_one_balance(base_currency)
    free_base_balance = ret
    return ret


# yeni pozisyon acmaya izin varmi
def is_left_free_pos():
    return len(open_positions) < poslimit


# girilen symbol open_positions in icinde varmi
def is_in_open_position(symbol):
    return symbol in [i["symbol"] for i in open_positions]


# satis yapilirken mevzu bahis symbolun ne kadar satilacagi bilgisini verir
def get_one_balance_from_open_positions(symbol):
    amount = 0
    try:
        amount = [i["amount"] for i in open_positions if i["symbol"] == symbol][0]
    except:
        pass

    return amount


# open_positions tan pozisyon siler , satis yapildiktan sonra cagirilir
def remove_from_open_positions(symbol):
    p = [i for i in open_positions if i["symbol"] == symbol][0]
    open_positions.remove(p)


# open_positions a pozisyon ekler , alim yapildiktan sonra cagirilir
def add_open_position(symbol, amount):
    open_positions.append(dict(symbol=symbol, amount=amount))


# bostaki base_currency miktarini doner
def get_base_free_balance():
    return free_base_balance


# acilacak pozisyonun buyuklugunu belirle (base_currency bazinda)
def get_pos_base_amount():
    if poslimit == len(open_positions):
        raise ValueError("pozisyon icin para yok")

    pos_base_amount = free_base_balance / (poslimit - len(open_positions))
    pos_base_amount = float("%.3f" % pos_base_amount)
    return pos_base_amount


def add_trade_history(symbol, type, amount, price, date=datetime.now()):
    t = dict(symbol=symbol, date=date, type=type, amount=amount, price=price)
    trade_history.append(t)

    if write_down_trade_history:
        th = deepcopy(trade_history)
        for i in th:
            i["date"] = i["date"].timestamp()
        with open("logs/trade_history", "w") as fp:
            json.dump(th, fp, indent=4)


# symbol : ETHUSDT
# coin_name : ETH
def get_one_balance_from_exchange(symbol=None, coin_name=None):
    ret = None
    b.get_all_balance()
    if symbol:
        ret = b.get_one_balance(symbol[:-len(base_currency)])
    elif coin_name:
        ret = b.get_one_balance(coin_name)
    return ret


# program baslangicinda borsadan guncel bilgileri ceker
def init():
    global open_positions
    open_positions = b.get_open_positions()
    update_free_base_balance()


init()
