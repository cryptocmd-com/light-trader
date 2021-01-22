import os
import logging

import binance

import market_data


logger = logging.getLogger(__name__)


market = market_data.MarketFeed(['btcusdt'])


async def get_client() -> binance.Client:
    client = binance.Client(
        os.environ.get('BINANCE_API_KEY'),
        os.environ.get('BINANCE_API_SECRET')
    )
    await client.load()
    return client


async def start():
    client = await get_client()
    market.register_for_candles(client)
    await client.start_market_events_listener()
