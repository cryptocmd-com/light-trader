import asyncio
import logging

from quart import Quart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)


@app.before_serving
async def startup():
    loop = asyncio.get_event_loop()
    logger.info('starting loop')


@app.route('/status')
async def hello():
    return {
        'overall': 'ok'
    }

if __name__ == '__main__':
    app.run()
