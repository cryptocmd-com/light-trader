import asyncio
import logging
import http

from dotenv import load_dotenv
from quart import Quart, abort
from quart_compress import Compress
import binance_trader

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Quart(__name__)
Compress(app)


@app.before_serving
async def startup():
    loop = asyncio.get_event_loop()
    loop.create_task(binance_trader.start())
    logger.info('starting loop')


@app.route('/status')
async def status():
    return {
        'overall': 'ok'
    }


@app.route('/market/candles/<symbol>')
async def symbol_candles(symbol: str):
    symbol_lc = symbol.lower()
    try:
        return {
            'candles': binance_trader.market.get_latest_candles_for_symbol(symbol_lc)
        }
    except KeyError:
        if symbol_lc not in binance_trader.market.symbols:
            abort(http.HTTPStatus.NOT_FOUND,
                  f'Not listening for symbol: {symbol}')
        raise


if __name__ == '__main__':
    app.run()
