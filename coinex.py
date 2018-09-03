import hashlib
import time
import collections
from datetime import datetime, timedelta
import requests
import json
from conf import getparam
from log import logprint


# coinex sembollerinde baz para sona yazılır eos-usdt için "EOSUSDT"

class CoinExApiError(Exception):
    pass


class CoinEx:
    _headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }

    def __init__(self, access_id=None, secret=None):
        self._access_id = access_id
        self._secret = secret

    def market_list(self):
        return self._v1('market/list')

    def market_ticker(self, market):
        return self._v1('market/ticker', market=market)

    def market_ticker_all(self):
        return self._v1('market/ticker/all')

    def market_depth(self, market, merge='0.00000001', **params):
        return self._v1('market/depth', market=market, merge=merge, **params)

    def market_deals(self, market):
        return self._v1('market/deals', market=market)

    def market_kline(self, market, type='1hour', **params):
        return self._v1('market/kline', market=market, type=type, **params)

    def balance(self):
        return self._v1('balance/', auth=True)

    def balance_coin_withdraw_list(self, **params):
        return self._v1('balance/coin/withdraw', auth=True, **params)

    def balance_coin_withdraw(self, coin_type, coin_address, actual_amount, **params):
        return self._v1('balance/coin/withdraw', method='post', auth=True, coin_type=coin_type,
                        coin_address=coin_address, actual_amount=actual_amount, **params)

    def balance_coin_withdraw_cancel(self, coin_withdraw_id, **params):
        return self._v1('balance/coin/withdraw', method='delete', auth=True, coin_withdraw_id=coin_withdraw_id,
                        **params)

    def order_limit(self, market, type, amount, price, **params):
        return self._v1('order/limit', method='post', auth=True, market=market, type=type, amount=amount, price=price,
                        **params)

    def order_market(self, market, type, amount, **params):
        return self._v1('order/market', method='post', auth=True, market=market, type=type, amount=amount, **params)

    def order_ioc(self, market, type, amount, price, **params):
        return self._v1('order/ioc', method='post', auth=True, market=market, type=type, amount=amount, price=price,
                        **params)

    def order_pending(self, market, page=1, limit=100):
        return self._v1('order/pending', method='get', auth=True, market=market, page=page, limit=limit)

    def order_finished(self, market, page=1, limit=100):
        return self._v1('order/finished', method='get', auth=True, market=market, page=page, limit=limit)

    def order_status(self, market, id):
        return self._v1('order/', method='get', auth=True, market=market, id=id)

    def order_deals(self, id, page=1, limit=100):
        return self._v1('order/deals', method='get', auth=True, id=id, page=page, limit=limit)

    def order_user_deals(self, market, page=1, limit=100):
        return self._v1('order/user/deals', method='get', auth=True, market=market, page=page, limit=limit)

    def order_pending_cancel(self, market, id):
        return self._v1('order/pending', method='delete', auth=True, market=market, id=id)

    def order_mining_difficulty(self):
        return self._v1('order/mining/difficulty', method='get', auth=True)

    def _v1(self, path, method='get', auth=False, **params):
        headers = dict(self._headers)

        if auth:
            if not self._access_id or not self._secret:
                raise CoinExApiError('API keys not configured')

            params.update(access_id=self._access_id)
            params.update(tonce=int(time.time() * 1000))

        params = collections.OrderedDict(sorted(params.items()))

        if auth:
            headers.update(Authorization=self._sign(params))

        if method == 'post':
            resp = requests.post('https://api.coinex.com/v1/' + path, json=params, headers=headers)
        else:
            fn = getattr(requests, method)
            resp = fn('https://api.coinex.com/v1/' + path, params=params, headers=headers)

        return self._process_response(resp)

    def _process_response(self, resp):
        resp.raise_for_status()

        data = resp.json()
        if data['code'] is not 0:
            raise CoinExApiError(data['message'])

        return data['data']

    def _sign(self, params):
        data = '&'.join([key + '=' + str(params[key]) for key in sorted(params)])
        data = data + '&secret_key=' + self._secret
        data = data.encode()
        return hashlib.md5(data).hexdigest().upper()


# todo fonksiyonlarin return formatlarini fxnlerin uzerine yaz
# Bu borsa classi abstract class
# baska borsalar icin bu class tamamen implement edilecek (fxn return degerleri ayni olmali)
class Borsa:
    def __init__(self, apikey, secret):
        self.coinex = CoinEx(apikey, secret)
        self.tickers = None
        self.balances = None
        self.exchange_datetime = None

        # init fxn
        self.get_all_balance()

    def get_tickers(self):
        url = "https://api.coinex.com/v1/market/ticker/all"
        r = requests.get(url)
        if r.status_code == 200:
            data = json.loads(r.text)["data"]
            dt = datetime.fromtimestamp(data["date"] // 1000)
            self.exchange_datetime = dt
            t = data["ticker"]
            d = [dict(symbol=i, last=float(t[i]["last"])) for i in t]
            return d

    def get_one_symbols_last_price(self, symbol, tickers=None):
        if tickers is None:
            tickers = self.tickers
        try:
            return [i for i in tickers if i["symbol"] == symbol][0]
        except:
            return None

    def update_tickers(self):
        self.tickers = self.get_tickers()

    def get_chart_data(self, symbol="BTCUSDT"):
        url = "https://api.coinex.com/v1/market/kline?market=%s&type=5min" % symbol.lower()
        r = requests.get(url)
        if r.status_code == 200:
            data = json.loads(r.text)["data"]
            data = [dict(date=i[0], open=i[1], close=i[2], high=i[3], low=i[4], volume=i[5]) for i in data]
            return data

    def get_all_balance(self):
        a = self.coinex.balance()
        balance = [dict(symbol=i, available=float(a[i]["available"])) for i in a]
        self.balances = balance
        return balance

    def get_one_balance(self, symbol):
        try:
            return [i for i in self.balances if i["symbol"] == symbol][0]["available"]
        except:
            return None

    def buy(self, symbol, amount_as_base_currency):
        try:
            return self.coinex.order_market(symbol, "buy", amount_as_base_currency)
        except CoinExApiError as e:
            logprint(e, symbol, amount_as_base_currency)
            return dict(status="undone", msg="order not handled")

    def sell(self, symbol, amount_as_target_currency):
        try:
            return self.coinex.order_market(symbol, "sell", amount_as_target_currency)
        except CoinExApiError as e:
            logprint(e, symbol, amount_as_target_currency)
            return dict(status="undone", msg="order not handled")

    def get_open_positions(self, base_currency="USDT", exclude_symbols=("BTC", "USDT", "CET")):
        return [dict(symbol="%s%s" % (i["symbol"], base_currency), amount=i["available"]) for i in self.balances if
                i["available"] > 0.00001 and i["symbol"] not in exclude_symbols]

    def get_symbol_list(self):
        return self.coinex.market_list()


access_id = getparam("access_id")
secret = getparam("secret")
borsa_instance = Borsa(access_id, secret)

