import typing
import asyncio
import logging
import itertools
from decimal import Decimal
import baseconv

from trade_plan import TradePlanAtUnspecifiedPrice
# from trade_plan_executor import TradePlanExecutor, TradeEventHandler
from market_data import MarketFeedEventHandler

logger = logging.getLogger(__name__)


class StrategyBase(
    MarketFeedEventHandler
):
    def __init__(self):
        self.position = Decimal(0)
        # TODO: Determine maximum position

        self._order_id_sequence = (
            f'{self.client_order_id_prefix}_{n:06}'
            for n in itertools.count(1)
        )

    @property
    def client_order_id_prefix(self) -> str:
        # TODO: Use a unique ID
        return baseconv.base58.encode(id(self))

    def generate_order_id(self) -> str:
        return next(self._order_id_sequence)

    def on_order_response(self, response: dict):
        'Called with the order execution info returned by Binance'
        order_id = response.get('clientOrderId')
        orig_qty = Decimal(response['origQty'])
        exec_qty = Decimal(response.get('executedQty', 0))
        transact_time = response.get('transactTime', 0)
        side = response.get('side')
        status = response.get('status', 'UNKNOWN')
        if orig_qty == exec_qty:
            if status.upper() != 'FILLED':
                raise ValueError(
                    f'Order {order_id} appears fully filled but status is {status}')
            logger.info(
                'Order %s filled %s %s at t=%d',
                order_id, side, exec_qty, transact_time)
        elif exec_qty > 0:
            logger.info(
                'Order %s partly filled %s %s/%s at t=%d. status: %s',
                order_id, side, exec_qty, orig_qty, transact_time, status)
        else:
            logger.info(
                'Order %s to %s %s not filled at t=%d. status: %s',
                order_id, side, orig_qty, transact_time, status)
            return

        # TODO: Calculate average fill price and commission.
        position_increment_sign = {
            'BUY': 1,
            'SELL': -1
        }[side]
        self.position += position_increment_sign * exec_qty
        return
