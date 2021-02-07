import os
import logging
import typing
import uuid

import toml
import binance

import market_data
import trade_plan_executor
import strategy_base


logger = logging.getLogger(__name__)

config = None
market = None
executor = None
connection_params = {}
strategies: typing.Dict[uuid.UUID, strategy_base.StrategyBase] = {}


async def get_client() -> binance.Client:
    extra_args = {}
    if connection_params.get('type') is None:
        logger.warning('No connection type is specified')
    if connection_params.get('type') != 'production':
        extra_args['endpoint'] = 'https://testnet.binance.vision'
    logger.info('Starting Binance client with extra args: %s', str(extra_args))

    client = binance.Client(
        connection_params['api_key'],
        connection_params['api_secret'],
        **extra_args
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


def load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'config.toml')
    global config
    config = toml.load(config_path)

    binance = config.get('binance', {})
    global connection_params
    connection_params = {
        'type': binance.get('connection', 'test'),
        'api_key': binance.get('api_key'),
        'api_secret': binance.get('api_secret')
    }


async def start():
    load_config()
    client = await get_client()
    global market
    market = market_data.MarketFeed(client)
    global executor
    executor = trade_plan_executor.TradePlanExecutor(client)
