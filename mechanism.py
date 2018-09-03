from strat import CoinStrat
from coinex import borsa_instance as b
from scheduler import Scheduler
from datetime import datetime
from log import logprint
from conf import getparam

# sepet = ['EOSUSDT', 'LFTUSDT', 'DASHUSDT', 'OLTUSDT', 'BCHUSDT', 'LTCUSDT', 'BTCUSDT', 'ETHUSDT', 'ETCUSDT',
# 'XRPUSDT','SCUSDT', 'XMRUSDT', 'ZECUSDT']

sepet = getparam("basket")

# stop_level_perc=8
# period_length=48
# degree_level=10
# trace_level=10
# target_rm_length=1

stop_level_perc = getparam("stop_level_perc")
period_length = getparam("period_length")
degree_level = getparam("degree_level")
trace_level = getparam("trace_level")
target_rm_length = getparam("target_rm_length")

coin_instance_list = [
    CoinStrat(i, b, stop_level_perc=stop_level_perc, period_length=period_length, degree_level=degree_level,
              trace_level=trace_level, target_rm_length=target_rm_length) for i in sepet]


class Mt(Scheduler):

    def short_task(self):
        b.update_tickers()
        for ctr, c in enumerate(coin_instance_list):
            c.short_per_task()
            print(sepet[ctr], c.last_price)

        print("short task executed", datetime.now().time())

    def long_task(self):
        for ctr, c in enumerate(coin_instance_list):
            c.long_per_task()
            print(sepet[ctr], c.current_target_low, c.current_target_high, c.current_degree)
            logprint(dict(symbol=sepet[ctr], target_low=c.current_target_low, target_high=c.current_target_high,
                          degree=c.current_degree))
        print("long task executed", datetime.now())


if __name__ == '__main__':

    for ctr1, c in enumerate(coin_instance_list):
        c.long_per_task()
        print(sepet[ctr1], c.current_target_low, c.current_target_high, c.current_degree)

    long_task_interval_min = getparam("long_task_interval_min")  # 5
    short_task_interval_sec = getparam("short_task_interval_sec")  # 5

    mt = Mt(long_task_interval_min, short_task_interval_sec)
    mt.start_as_loop()

