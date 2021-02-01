import os
import logging
import typing
import uuid

import binance

import market_data
import trade_plan_executor
import strategy_base


logger = logging.getLogger(__name__)

market = None
executor = None
strategies: typing.Dict[uuid.UUID, strategy_base.StrategyBase] = {}


async def get_client() -> binance.Client:
    client = binance.Client(
        os.environ.get('BINANCE_API_KEY'),
        os.environ.get('BINANCE_API_SECRET')
    )
    await client.load()
    return client


def add_strategy(
    input_symbols: typing.Sequence[str],
    strategy: strategy_base.StrategyBase
) -> uuid.UUID:
    new_uuid = uuid.uuid1()
    strategies[new_uuid] = strategy
    for symbol in input_symbols:
        # FIXME: Roll-back if registration fails after registering
        # only some symbols.
        market.register_handler(symbol.upper(), strategy)

    logger.info(
        'Strategy of class %s registered successfully with UUID %s',
        strategy.__class__.__name__, new_uuid)
    return new_uuid


async def start():
    client = await get_client()
    global market
    market = market_data.MarketFeed(client)
    global executor
    executor = trade_plan_executor.TradePlanExecutor(client)
