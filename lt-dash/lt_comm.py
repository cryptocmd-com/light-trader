from requests.auth import HTTPBasicAuth
import requests
import pandas as pd
from decimal import Decimal

def get_candle_history(symbol):
    url = 'https://api.binance.com/api/v3/klines?symbol={}&interval=1m&limit=1000'.format(symbol)

    columns = ['Open_time', 'Open' ,'High', 'Low', 'Close', 'Volume', 'Close_time', 
    'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume',
    'Ignore']

    responde = requests.get(url=url)
    responde = responde.json()
    df = pd.DataFrame(data=responde, columns=columns)
    df['Close_time'] = pd.to_datetime(df['Close_time'], unit='ms')
    df = df.set_index(keys=df['Close_time'])

    return df[['Open' ,'High', 'Low', 'Close', 'Volume']]


def get_last_candle_info(symbol):
    server_url = 'http://127.0.0.1:5000'
    path = '/market/candles/{}'.format(symbol)
    responde = requests.get(url=server_url + path)
    responde = responde.json()
    candle = pd.DataFrame(data=responde['candles'])
    candle['open'] = candle['open_price'].astype(float)
    candle['low'] = candle['low_price'].astype(float)
    candle['high'] = candle['high_price'].astype(float)
    candle['close'] = candle['close_price'].astype(float)
    return candle[['open', 'low', 'high', 'close']]


def get_strategy_info(key, s_id):
    path = '/strategy_advice/telegram/{}'.format(s_id)
    responde = send_get_req(key=key, path=path)
    responde = responde.json()
    responde_df = pd.DataFrame(data=responde, index=[0])
    responde_df['position'] = responde_df['position'].astype(float)
    return responde_df[['create_time', 'symbol', 'entry', 'quantity', 'SL1', 'TP1', 'position', 'status']]


def get_general_positions_info(key):
    path = '/strategy_advice/telegram/'
    responde = send_get_req(key=key, path=path)
    responde = responde.json()
    strategies = responde['strategies']
    strategies_df = pd.DataFrame(data=strategies)
    strategies_df['position'] = strategies_df['position'].astype(float)
    return strategies_df.drop('url', axis=1)


def get_server_status(key):
    path = '/status'
    responde = send_get_req(key=key, path=path)
    return responde.text.replace('{', '').replace('}', '').replace('"', '').split(':')[-1]


def send_get_req(key, path):
    auth=HTTPBasicAuth(key[0], key[1])
    url = 'http://127.0.0.1:5000/{}'.format(path)
    responde = requests.get(url=url, auth=auth)
    return responde