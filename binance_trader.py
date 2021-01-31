import os
import logging

import binance

import market_data
import trade_plan_executor
import strategy_external


logger = logging.getLogger(__name__)

market = None


async def get_client() -> binance.Client:
    client = binance.Client(
        os.environ.get('BINANCE_API_KEY'),
        os.environ.get('BINANCE_API_SECRET')
    )
    await client.load()
    return client


async def start():
    client = await get_client()
    global market
    market = market_data.MarketFeed(client)
    executor = trade_plan_executor.TradePlanExecutor(client)
    strategy = strategy_external.StrategyExternal(executor)
    market.register_handler('BTCUSDT', strategy)
    await client.start_market_events_listener()
