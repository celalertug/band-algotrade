import json
from datetime import datetime, timedelta
import os
import requests


def download_one(symbol="USDT_BTC", savedir="chartdata", period=300, start_timestamp=1405699200,
                 end_timestamp=9999999999):
    # symbol = "USDT_ETH"
    url = "https://poloniex.com/public?command=returnChartData&currencyPair=%s&start=%d&end=%d&period=%d" % (
        symbol, start_timestamp, end_timestamp, period)
    r = requests.get(url)
    if r.status_code == 200:
        with open("%s/%s" % (savedir, symbol), "w") as fp:
            fp.write(r.text)
            print(symbol, savedir, "saved")


def download_all(savedir="chartdata/usdt", period=300):
    basket = ['USDT_BTC', 'USDT_DASH', 'USDT_LTC', 'USDT_NXT', 'USDT_STR', 'USDT_XMR', 'USDT_XRP', 'USDT_ETH',
              'USDT_ETC', 'USDT_REP', 'USDT_ZEC', 'USDT_BCH', 'USDT_EOS']
    for i in basket:
        download_one(i, savedir, period=period)


if __name__ == '__main__':
    download_all("chartdata/usdt_daily", period=60 * 60 * 24)
