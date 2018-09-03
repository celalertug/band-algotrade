from datetime import datetime, timedelta
from pandas import DataFrame, Series
from copy import deepcopy
import math
import numpy as np
from coinex import borsa_instance as b
from orderhandler import sell_order, buy_order


def nop():
    pass


# parametreler dosyadan okunacak

class CoinStrat:
    def __init__(self, symbol, borsa, **kwargs):
        self.symbol = symbol

        # long per task vars
        self.current_degree = 0
        self.current_target_high = 0
        self.current_target_low = 0

        # short per task vars
        self.hold = 0  # startup fonksiyonu ile bu bilgiyi borsadan cek
        self.stop_price = 0
        self.last_price = 0

        # parametreler
        self.stop_level_perc = kwargs.get("stop_level_perc", 8)
        self.period_length = kwargs.get("period_length", 48)
        self.degree_level = kwargs.get("degree_level", 10)
        self.trace_level = kwargs.get("trace_level", 10)
        self.target_rm_length = kwargs.get("target_rm_length", 1)

        self.b = borsa

    def get_degree(self, df, periot_length=48, degree_level=10):

        per_len = periot_length
        df["rm"] = df.close.rolling(per_len * degree_level).mean()
        df["rm_normal"] = df.rm / df.rm[df.rm.first_valid_index()] * 100
        df["rm_normal_past"] = df.rm_normal.shift(per_len * degree_level)
        df["rm_diff"] = df.rm_normal - df.rm_normal_past
        df["rad"] = np.arctan(df.rm_diff / (per_len * degree_level))
        df["degree"] = (df.rad * 180) / math.pi

        all_order = df[['close', 'date', 'high', 'low', 'open', 'volume', 'degree']]
        self.current_degree = df.degree.values[-1]
        return deepcopy(all_order)

    def get_targets(self, df, periot_length=48, trace_level=10, target_rm_length=1):
        df["target_high"] = df.high.shift(periot_length * trace_level)
        df["target_high2"] = df.target_high.rolling(periot_length).max()
        df["target_high3"] = df.target_high2.rolling(target_rm_length).mean()

        df["target_low"] = df.low.shift(periot_length * trace_level)
        df["target_low2"] = df.target_low.rolling(periot_length).min()
        df["target_low3"] = df.target_low2.rolling(target_rm_length).mean()

        self.current_target_high = df.target_high3.values[-1]
        self.current_target_low = df.target_low3.values[-1]

        return deepcopy(df)

    def long_per_task(self):
        # a = self.b.get_chart_data(start_dt=datetime.now() - timedelta(days=4))
        a = self.b.get_chart_data(self.symbol)
        df = DataFrame(a)
        df.date = df.date.apply(datetime.fromtimestamp)
        self.get_degree(df, self.period_length, self.degree_level)
        self.get_targets(df, self.period_length, self.trace_level, self.target_rm_length)
        nop()

    def short_per_task(self):
        # t = self.b.get_tickers()
        price = self.last_price = self.b.get_one_symbols_last_price(self.symbol)
        if self.hold == 0 and self.current_degree > 0 and price["last"] > self.current_target_high:
            self.hold = 1
            self.stop_price = price["last"] * (1 - self.stop_level_perc / 100)
            buy_order(self.symbol)

        elif self.hold == 1 and (price["last"] < self.current_target_low or price["last"] < self.stop_price):
            self.hold = 0
            sell_order(self.symbol)


if __name__ == '__main__':
    # b = Borsa(None, None)
    c = CoinStrat("BTCUSDT", borsa=b)
    b.update_tickers()
    c.long_per_task()
    c.short_per_task()
