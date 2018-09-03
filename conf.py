import json

default = {'base_currency': 'USDT',
           'poslimit': 6,
           'write_down_trade_history': True,
           'access_id': 'coinex access id',
           'secret': 'coinex secret',
           'long_task_interval_min': 5,
           'short_task_interval_sec': 5,
           'basket': ['EOSUSDT',
                     'LFTUSDT',
                     'DASHUSDT',
                     'OLTUSDT',
                     'BCHUSDT',
                     'LTCUSDT',
                     'BTCUSDT',
                     'ETHUSDT',
                     'ETCUSDT',
                     'XRPUSDT',
                     'SCUSDT',
                     'XMRUSDT',
                     'ZECUSDT'],
           'stop_level_perc': 8,
           'period_length': 48,
           'degree_level': 10,
           'trace_level': 10,
           'target_rm_length': 1}

current_config = None


def make_default():
    with open("config.json", "w") as fp:
        json.dump(default, fp, indent=4)


def load_config():
    global current_config
    with open("config.json", "r") as fp:
        current_config = json.load(fp)


def getparam(key):
    return current_config.get(key)


load_config()
if __name__ == '__main__':
    a = getparam("trace_level1")
