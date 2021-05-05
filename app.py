import asyncio
import logging
import collections
import datetime
import http
import os


import quart.flask_patch
from quart import (
    Quart, abort, request, jsonify, url_for
)
from quart_compress import Compress

import binance_trader
import strategy_external_advice
from auth import auth
from strategy_journal import strategyJournal, make_journal_dir, strategy_journal

def get_logging_level() -> int:
    default_log_level = 'INFO'
    config = binance_trader.read_config()
    logging_section = collections.ChainMap(
        config.get('logging', {}),
        {'level': default_log_level}
    )
    logging_level = getattr(
        logging,
        logging_section['level'].upper(),
        getattr(logging, default_log_level)
    )
    return logging_level


logger = logging.getLogger(__name__)
log_file_name = 'log/' + str(int(datetime.datetime.now().timestamp())) + '.log'
log_level = get_logging_level()
f = open(log_file_name, "x")
logging.basicConfig(
    level= log_level,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    datefmt='%d-%m %H:%M',
    filename= log_file_name,
    filemode='w')

console = logging.StreamHandler()
console.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)



app = Quart(__name__)
Compress(app)


@app.before_serving
async def startup():
    loop = asyncio.get_event_loop()
    loop.create_task(binance_trader.start())
    logger.info('starting loop')


@app.errorhandler(http.HTTPStatus.NOT_FOUND)
def resource_not_found(e):
    return jsonify(error=e.description), http.HTTPStatus.NOT_FOUND


@app.errorhandler(http.HTTPStatus.BAD_REQUEST)
def bad_request(e):
    return jsonify(error=e.description), http.HTTPStatus.BAD_REQUEST


@app.route('/status')
async def status():
    return {
        'overall': 'ok'
    }


@app.route('/strategy_advice/telegram/', methods=['POST'])
@auth.login_required
async def strategy_advice_telegram_add():
    request_json = await request.get_json(force=True)
    symbols = request_json.get('symbols', [])
    if 'symbol' in request_json and request_json['symbol'] not in symbols:
        symbols.append(request_json['symbol'])

    if not symbols:
        abort(
            http.HTTPStatus.BAD_REQUEST,
            'No symbol(s) specified in the request')
    try:
        new_strategy = strategy_external_advice.StrategyExternalAdvice(
            binance_trader.client,
            request_json
        )
        new_strategy_id = binance_trader.add_strategy(symbols, new_strategy)
        strategy_journal.create_strategy_journal(new_strategy, new_strategy_id)
        return (
            new_strategy.state,
            http.HTTPStatus.CREATED,
            {'Location': url_for(
                'strategy_advice_telegram_get', strategy_id=new_strategy_id)}
        )
    except (ValueError, TypeError, ArithmeticError) as e:
        logger.exception(
            "Strategy advice rejected as malformed or semantically invalid")
        abort(http.HTTPStatus.BAD_REQUEST, str(e))


def _add_strategy_url(strategy_info: dict) -> dict:
    strategy_id = strategy_info.get('strategy_id')
    if strategy_id is not None:
        strategy_info['url'] = url_for(
                'strategy_advice_telegram_get', strategy_id=strategy_id)
    return strategy_info


@app.route('/strategy_advice/telegram/', methods=['GET'])
@auth.login_required
def strategy_advice_telegram_list():
    listing = binance_trader.get_strategy_summaries(
            (strategy_external_advice.StrategyExternalAdvice,))

    return (
        {'strategies': list(map(_add_strategy_url, listing))},
        http.HTTPStatus.OK
    )


@app.route('/strategy_advice/telegram/<strategy_id>', methods=['GET'])
@auth.login_required
async def strategy_advice_telegram_get(strategy_id):
    strategy = binance_trader.strategies.get(strategy_id)
    if strategy is None:
        abort(http.HTTPStatus.NOT_FOUND, f'No strategy with id {strategy_id}')
    return (
        strategy.state,
        http.HTTPStatus.OK
    )


@app.route('/strategy_advice/telegram/<strategy_id>/status', methods=['PUT', 'GET']) 
@auth.login_required
async def strategy_advice_telegram_status(strategy_id):
    strategy = binance_trader.strategies.get(strategy_id)
    if strategy is None:
        abort(http.HTTPStatus.NOT_FOUND, f'No strategy with id {strategy_id}')

    new_status = None
    if request.method == 'PUT':
        try:
            req = await request.get_json()
            new_status = req['status']
            strategy.set_status(new_status)
            strategy_journal.update_strategy_status(strategy_id=strategy_id, state=strategy.state , new_status=new_status)
        except (ValueError, AttributeError):
            abort(http.HTTPStatus.BAD_REQUEST, f'Unknown status: {new_status}')
        except KeyError:
            abort(http.HTTPStatus.BAD_REQUEST, f'Request did not specify a status')


    return (
        {
            "status": strategy.state['status']
        },
        http.HTTPStatus.OK
    )


    


@app.route('/market/candles/<symbol>')
async def symbol_candles(symbol: str):
    symbol_uc = symbol.upper()
    try:
        return {
            'candles': binance_trader.market.get_latest_candles_for_symbol(symbol_uc)
        }
    except KeyError:
        if symbol_uc not in binance_trader.market.symbols:
            abort(http.HTTPStatus.NOT_FOUND,
                  f'Not listening for symbol: {symbol}')
        raise


if __name__ == '__main__':
    # FIXME: Configure the level from TOML
    # logging.basicConfig(level=logging.DEBUG)
    app.run()
