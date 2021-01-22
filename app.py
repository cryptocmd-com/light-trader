import asyncio
import logging

from dotenv import load_dotenv
from quart import Quart
import binance_trader

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Quart(__name__)


@app.before_serving
async def startup():
    loop = asyncio.get_event_loop()
    loop.create_task(binance_trader.start())
    logger.info('starting loop')


@app.route('/status')
async def hello():
    return {
        'overall': 'ok'
    }

if __name__ == '__main__':
    app.run()
