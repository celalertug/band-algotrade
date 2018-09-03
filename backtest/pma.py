from pandas import DataFrame, Series
from datetime import datetime, timedelta
from time import strptime
import json


def get_slip(seri):
    #
    # pandas.Series dizisinde en buyuk kaymayi bulur
    #

    top = 0
    status = "none"
    arr = []
    all_arr = []

    for i in range(len(seri)):
        if seri[i] > top:
            if status == "back":
                status = "none"
                all_arr.append(arr)
                arr = []

            top = seri[i]
        else:
            status = "back"
            arr.append(i)

    if status == "back":
        all_arr.append(arr)

    fiyat, t1, b1 = 0, 0, 0

    for i in all_arr:
        start = i[0] - 1
        end = i[-1]
        if start > 0 and end > 0:
            t = seri[start:end].max()
            b = seri[start:end].min()
            min_index = seri[start:end].idxmin()
            if abs(t - b) > fiyat:
                t1, b1, fiyat = start, min_index, (t - b)

    return {
        "start_index": t1,
        "min_index": b1,
        "amount": fiyat
    }


def str2dt(str_dt):
    a = strptime(str_dt.split(".")[0], "%Y-%m-%dT%H:%M:%S")
    return datetime(a.tm_year, a.tm_mon, a.tm_mday, a.tm_hour, a.tm_min, a.tm_sec)


def performance_pma(trade_history_df, giris_sermayesi=1000, poslimit=6):
    if not isinstance(trade_history_df, DataFrame):
        raise ValueError("trade history dataframe olmali")
    pass
    # history2 = DataFrame(history)
    history2 = trade_history_df

    # extract_most_profit_len = 0

    history2["marj"] = history2.close_price / history2.open_price
    history2["profit"] = (history2.close_price - history2.open_price) * history2["amount"]
    history2["pos_time"] = history2.close_date - history2.open_date
    # if extract_most_profit_len:
    #     ix = history2.sort_values("marj").marj.index[-extract_most_profit_len:]
    #     history2 = history2[~history2.index.isin(ix)].reset_index()

    last_valid_index = history2.last_valid_index()
    first_valid_index = history2.first_valid_index()

    history2["profile"] = history2.estimated_balance / giris_sermayesi
    test_duration = history2.close_date[last_valid_index] - history2.open_date[first_valid_index]
    active_rate = ((history2.close_date - history2.open_date).sum() / poslimit) / test_duration
    net_profit = history2.profit.sum()
    gross_profit = history2.profit[history2.profit > 0].sum()
    gross_loss = history2.profit[history2.profit < 0].sum()
    profit_factor = abs(gross_profit / gross_loss)
    numberof_trade = len(history2)
    most_profit_trade = history2.profit.max()
    most_loss_trade = history2.profit.min()
    most_profit_trade_percent = most_profit_trade / net_profit * 100
    profit_per_trade = history2.profit.mean()
    profit_per_profitable_trade = history2.profit[history2.profit > 0].mean()
    loss_per_loss_trade = history2.profit[history2.profit < 0].mean()
    risk_reward = abs(profit_per_profitable_trade / loss_per_loss_trade)
    success_rate = len(history2.profit[history2.profit > 0]) / numberof_trade
    avg_pos_time = history2.pos_time.mean()

    capital_return = history2.profile[last_valid_index]
    max_reduction_value = get_slip(history2.profile)["amount"]
    reduction_rate = capital_return / max_reduction_value
    sharp = capital_return / history2.profile.std()

    sepet = list(set([i["name"] for i in all_orders]))
    hodl = []
    for name in sepet:
        first_price = [i for i in all_orders if i["name"] == name][0]["price"]
        last_price = [i for i in all_orders if i["name"] == name][-1]["price"]
        hodl_marj = last_price / first_price
        hodl.append(hodl_marj)
    hodl = sum(hodl) / len(hodl)

    performance = dict(test_duration=test_duration, active_rate=active_rate, net_profit=net_profit,
                       gross_profit=gross_profit,
                       gross_loss=gross_loss, profit_factor=profit_factor, numberof_trade=numberof_trade,
                       most_profit_trade=most_profit_trade, most_loss_trade=most_loss_trade,
                       most_profit_trade_percent=most_profit_trade_percent, profit_per_trade=profit_per_trade,
                       risk_reward=risk_reward, success_rate=success_rate, avg_pos_time=avg_pos_time,
                       capital_return=capital_return, max_reduction_value=max_reduction_value,
                       reduction_rate=reduction_rate, sharp=sharp, hodl=hodl)

    return performance


# portfoy managemet algo
def pma(all_orders, giris_sermaye=1000, poslimit=6):
    pass

    if set(all_orders[0].keys()) != {'price', 'date', 'name', 'type'}:
        raise ValueError("price date name type degil")

    if not isinstance(all_orders[0]["date"], datetime):
        raise ValueError("date datetime objesi olacak")

    all_orders = sorted(all_orders, key=lambda k: k["date"])

    base_balance = giris_sermaye
    estimated_balance = 0

    open_positions = []
    history = []

    for ctr, i in enumerate(all_orders):
        now = i
        if i["name"] not in [j["name"] for j in open_positions]:
            if len(open_positions) < poslimit and i["type"] == "buy":
                pass
                pos_base_amount = base_balance / (poslimit - len(open_positions))
                base_balance -= pos_base_amount
                amount = pos_base_amount / i["price"]
                pos = dict(date=i["date"], open_index=ctr, price=i["price"], name=i["name"], amount=amount)
                # print("alim", pos)
                open_positions.append(pos)

        if i["name"] in [j["name"] for j in open_positions] and len(open_positions) > 0 and i["type"] == "sell":
            pass
            pos = [j for j in open_positions if j["name"] == i["name"]][0]
            pos_base_amount = pos["amount"] * i["price"]
            base_balance += pos_base_amount

            open_positions.remove(pos)

            estimated_balance = sum([j["price"] * j["amount"] for j in
                                     open_positions]) + base_balance  # toplam assetlerin base para karsiligini bulur

            oi = pos["open_index"]
            t = dict(open_price=all_orders[oi]["price"], open_date=all_orders[oi]["date"], close_price=i["price"],
                     close_date=i["date"], name=i["name"], amount=pos["amount"], open_pos_count=len(open_positions),
                     base_balance=base_balance, estimated_balance=estimated_balance)
            # print("satis", pprint(t))
            history.append(t)

    history2 = DataFrame(history)
    return history2


def convert_onestrat_orders(order_path="all_orders", start_dt=None, end_dt=None):
    with open(order_path, "r") as fp:
        all_orders = json.load(fp)
        for i in all_orders:
            i["open_date"] = str2dt(i["open_date"])
            i["close_date"] = str2dt(i["close_date"])

        # df = DataFrame(all_orders)

    all_orders = sorted(all_orders, key=lambda k: k["open_date"])
    if start_dt:
        all_orders = [i for i in all_orders if i["open_date"] > start_dt]
    if end_dt:
        all_orders = [i for i in all_orders if i["open_date"] < end_dt]

    if set(all_orders[0].keys()) != {'close_date', 'close_price', 'name', 'open_date', 'open_price'}:
        raise ValueError("all order formati uygun degil")

    if start_dt:
        pass

    sorted_order = []
    for i in all_orders:
        e1 = dict(price=i["open_price"], date=i["open_date"], name=i["name"], type="buy")
        e2 = dict(price=i["close_price"], date=i["close_date"], name=i["name"], type="sell")
        sorted_order.append(e1)
        sorted_order.append(e2)

    all_orders = sorted(sorted_order, key=lambda k: k["date"])
    return all_orders


if __name__ == '__main__' and 1:  # fixed parameter optimisation
    pass
    all_orders = convert_onestrat_orders("all_orders", datetime.now() - timedelta(days=120))
    history = pma(all_orders, 1000, 6)
    performance = performance_pma(history)
