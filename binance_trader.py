import os
import logging
import typing
import uuid

import toml
import binance

import market_data
import strategy_base
import auth


logger = logging.getLogger(__name__)

config = None
market = None
client = None
connection_params = {}
user_passwords: typing.Dict[str, str] = {}
strategies: typing.Dict[str, strategy_base.StrategyBase] = {}


async def get_client() -> binance.Client:
    extra_args = {}
    if connection_params.get('type') is None:
        logger.warning('No connection type is specified')
    if connection_params.get('type').lower() != 'live':
        extra_args['endpoint'] = 'https://testnet.binance.vision'
    logger.info('Starting Binance client with extra args: %s', str(extra_args))

    client = binance.Client(
        connection_params['api_key'],
        connection_params['api_secret'],
        **extra_args
    )
    await client.load()
    return client


# FIXME: Use a shorter identifier which can be encoded into client order IDs.
# E.g.: A 32-bit integer encoded as base58 (6 characters)
# using e.g.: https://pypi.org/project/python-baseconv/


def add_strategy(
    input_symbols: typing.Sequence[str],
    strategy: strategy_base.StrategyBase
) -> str:
    for symbol in input_symbols:
        # FIXME: Roll-back if registration fails after registering
        # only some symbols.
        market.register_handler(symbol.upper(), strategy)

    logger.info(
        'Strategy of class %s registered successfully with ID %s',
        strategy.__class__.__name__, strategy.client_order_id_prefix)
    strategies[strategy.client_order_id_prefix] = strategy
    return strategy.client_order_id_prefix


def get_strategy_summaries(restrict_classes=()) -> typing.Generator[
    typing.Dict[str, typing.Any],
    None,
    None
]:
    for strategy in strategies.values():
        if not restrict_classes or isinstance(strategy, restrict_classes):
            yield strategy.summary


def read_config():
    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'config.toml')
    return toml.load(config_path)


def load_config():
    global config
    config = read_config()

    binance = config.get('binance', {})
    global connection_params
    connection_params = {
        'type': binance.get('connection', 'test'),
        'api_key': binance.get('api_key'),
        'api_secret': binance.get('api_secret')
    }

    global user_passwords
    user_passwords = config.get('user_passwords', {})
    auth.setup_auth(user_passwords)


async def on_order_executed(
    execution_report: binance.events.OrderUpdateWrapper
):
    logger.info('Order executed %s', execution_report)


async def start():
    load_config()
    global client
    client = await get_client()
    global market
    market = market_data.MarketFeed(client)
