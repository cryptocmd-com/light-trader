import os
import logging

import binance


logger = logging.getLogger(__name__)


async def get_client() -> binance.Client:
    client = binance.Client(
        os.environ.get('BINANCE_API_KEY'),
        os.environ.get('BINANCE_API_SECRET')
    )
    await client.load()
    return client


def on_kline(event):
    logger.info(f"Got kline. Closed: {event.kline_closed}")


def register_for_candles(
    client: binance.Client
):
    client.events.register_event(
        on_kline,
        "btcusdt@kline_1m"
    )


async def start(loop):
    client = await get_client()
    register_for_candles(client)
    loop.create_task(client.start_market_events_listener())
