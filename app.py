import asyncio
import logging
import http

import quart.flask_patch
from quart import Quart, abort, request, jsonify
from quart_compress import Compress

import binance_trader
import strategy_external_advice
from auth import auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
async def strategy_advice_telegram():
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
            binance_trader.executor,
            request_json
        )
        new_strategy_uuid = binance_trader.add_strategy(symbols, new_strategy)
        return (
            {'strategy_uuid': new_strategy_uuid},
            http.HTTPStatus.CREATED)
    except (ValueError, TypeError, ArithmeticError) as e:
        logger.exception(
            "Strategy advice rejected as malformed or semantically invalid")
        abort(http.HTTPStatus.BAD_REQUEST, str(e))


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
    app.run()
