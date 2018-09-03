import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame, Series
from copy import deepcopy
import numpy as np
import math
import os
import json


def get_degree(df, periot_length=48, degree_level=20):
    # if __name__ == '__main__':
    #     pass
    #     periot_length = 48
    #     degree_level = 20

    df["degree_close"] = df.close.shift(1)
    df["rm"] = df.degree_close.rolling(periot_length * degree_level).mean()
    df["rm_normal"] = df.rm / df.rm[df.rm.first_valid_index()] * 100
    df["rm_normal_past"] = df.rm_normal.shift(periot_length * degree_level)
    df["rm_diff"] = df.rm_normal - df.rm_normal_past
    df["rad"] = np.arctan(df.rm_diff / (periot_length * degree_level))
    df["degree"] = (df.rad * 180) / math.pi

    # df = df.drop(columns=["rm", "rm_normal", "rm_normal_past", "rm_diff", "rad"])
    del df["rm"]
    del df["rm_normal"]
    del df["rm_normal_past"]
    del df["rm_diff"]
    del df["rad"]

    return df


def get_raw_order(df, periot_length=48, trace_length=19, target_rm_length=7, degree_level=20, stop_trace_perc=8,
                  fee_perc=0.1, slip_perc=0.5):
    # if __name__ == '__main__' and 1:
    #     periot_length = 48
    #     trace_length = 19
    #     target_rm_length = 7
    #     degree_level = 20
    #     stop_trace_perc = 8
    #     fee_perc = 0.1
    #     slip_perc = 0.5
    per_len = periot_length  # 5
    trace_len = trace_length  # 3
    target_rm_len = target_rm_length  # uygulamamak icin 1 girilir

    df = get_degree(df, per_len, degree_level)

    df["target_high"] = df.high.shift(per_len * trace_len + 1)
    df["target_high2"] = df.target_high.rolling(per_len).max()
    df["target_high3"] = df.target_high2.rolling(target_rm_len).mean()

    del df["target_high"]
    del df["target_high2"]
    df = df.rename(columns={'target_high3': 'target_high'})

    df["ifhigh"] = (df.high > df.target_high) & (df.degree > 0)
    df["ifhigh_cross"] = (df.ifhigh != df.ifhigh.shift(1)) & df.ifhigh

    df["open_price"] = df[df.ifhigh_cross]["target_high"]

    ix = df[(df.open > df.target_high) & (df.degree > 0) & df.ifhigh_cross].index
    df.iloc[ix, df.columns.get_loc("open_price")] = df.loc[ix]["open"]

    df["open_price"] = df["open_price"] * (1 + fee_perc / 100) * (1 + slip_perc / 100)
    df["stop"] = df["open_price"] * (1 - stop_trace_perc / 100)
    df["stop"] = df["stop"].fillna(method="ffill")

    #####################################################################################################
    #
    df["target_low"] = df.low.shift(per_len * trace_len)
    df["target_low2"] = df.target_low.rolling(per_len).min()
    df["target_low3"] = df.target_low2.rolling(target_rm_len).mean()

    del df["target_low"]
    del df["target_low2"]
    df = df.rename(columns={'target_low3': 'target_low'})

    if stop_trace_perc:
        df["iflow"] = (df.low < df.target_low) | (df.low < df.stop)  # stop var
    else:
        df["iflow"] = (df.low < df.target_low)  # stop yok

    df["iflow_cross"] = (df.iflow != df.iflow.shift(1)) & df.iflow

    df["sell_price"] = df[df.iflow_cross]["target_low"]

    ix = df[df.stop > df.target_low].index
    df.iloc[ix, df.columns.get_loc("sell_price")] = df.loc[ix]["stop"]

    ix = df[(df.open < df.stop) | (df.open < df.target_low)].index
    df.iloc[ix, df.columns.get_loc("sell_price")] = df.loc[ix]["open"]

    df["sell_price"] = df["sell_price"] * (1 - fee_perc / 100) * (1 - slip_perc / 100)

    # #####################################################################################################

    dfor = DataFrame()
    dfor["open"] = df.ifhigh_cross
    dfor["close"] = df.iflow_cross

    op = dfor.open.values
    cl = dfor.close.values

    hold = 0
    for i in range(len(op)):
        if hold == 0:
            if op[i]:
                hold = 1
            if cl[i]:
                cl[i] = False
        else:
            if cl[i]:
                hold = 0
            if op[i]:
                op[i] = False

    dfor["open"] = op
    dfor["close"] = cl

    open_index = dfor[dfor.open].index
    close_index = dfor[dfor.close].index

    df["emir"] = np.nan
    df.iloc[open_index, df.columns.get_loc("emir")] = "al"
    df.iloc[close_index, df.columns.get_loc("emir")] = "sat"

    df.iloc[df[(df.emir == "sat") & (df.open_price.notnull())].index, df.columns.get_loc("open_price")] = np.nan
    df.iloc[df[(df.emir == "al") & (df.open_price.notnull())].index, df.columns.get_loc("sell_price")] = np.nan

    all_order = df[
        ['close', 'date', 'high', 'low', 'open', 'volume', 'open_price', 'sell_price', 'emir', "degree"]]
    all_order = all_order.loc[open_index.union(close_index)]
    if not all_order.empty:
        if all_order.emir.values[-1] == "al":  # son emir al olamaz
            all_order = all_order[:-1]

    return deepcopy(all_order)


def get_orderlist(df_raw_order):
    # if __name__ == '__main__' and 1:
    #     print("sm")

    sell_index = df_raw_order[df_raw_order.sell_price.notnull()].index
    buy_index = df_raw_order[df_raw_order.open_price.notnull()].index

    ord = DataFrame()
    ord["open_price"] = df_raw_order.loc[buy_index]["open_price"].values
    ord["open_date"] = df_raw_order.loc[buy_index]["date"].values
    ord["close_price"] = df_raw_order.loc[sell_index]["sell_price"].values
    ord["close_date"] = df_raw_order.loc[sell_index]["date"].values

    # ord["marj"] = ord.close_price / ord.open_price
    # ord["profil"] = ord.marj.cumprod()

    return deepcopy(ord)


if __name__ == '__main__' and 1:  # tum orderdf ler birlestir. fixed paramterers for one coin
    print("sm")
    dr = "chartdata/usdt"
    li = os.listdir(dr)

    all_orderdf = DataFrame()
    for ctr, i in enumerate(li):
        print(i)
        pth = "%s/%s" % (dr, i)
        df = pd.read_json(pth)
        raworder = get_raw_order(df, 48, 19, 1, 20, 8, 0.1, 0.5)
        orderdf = get_orderlist(raworder)
        orderdf["name"] = i
        all_orderdf = pd.concat([all_orderdf, orderdf])

    all_orderdf = all_orderdf.sort_values("open_date").reset_index().drop(columns=["index"])

    with open("all_orders", "w") as fp:
        a = [dict(open_price=i[0], open_date=str(i[1]), close_price=i[2], close_date=str(i[3]), name=i[4]) for i in
             zip(all_orderdf.open_price.values, all_orderdf.open_date.values, all_orderdf.close_price.values,
                 all_orderdf.close_date.values, all_orderdf.name.values)]
        json.dump(a, fp, indent=4)
