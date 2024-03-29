import abc
import typing
import logging
import baseconv
import datetime
import itertools
import dataclasses
import collections
from decimal import Decimal
from enum import Enum, auto
from strategy_journal import strategy_journal


from trade_plan import TradePlanAtUnspecifiedPrice
# from trade_plan_executor import TradePlanExecutor, TradeEventHandler
from market_data import MarketFeedEventHandler

logger = logging.getLogger(__name__)


class StrategyBase(
    MarketFeedEventHandler
):
    class Status(Enum):
        STOPPED = auto()
        ACTIVE = auto() 
        PAUSED = auto()
        FAILED = auto()
        COMPLETE = auto()

    def __init__(self):
        self.position = Decimal(0)
        self.actual_averege_entry_price = None
        self.create_time = datetime.datetime.now().replace(microsecond=0).isoformat()
        self.status = self.Status.PAUSED
        # TODO: Determine maximum position

        self._order_id_sequence = (
            f'{self.client_order_id_prefix}_{n:06}'
            for n in itertools.count(1)
        )

    def set_status(self, new_status) -> None:
        try:
            self.status = self.Status[new_status]
        except KeyError as ex:
            raise ValueError(f'Invalid status {new_status}') from ex

    @property
    def state(self) -> typing.Dict[str, typing.Any]:
        return {
            'strategy_id': self.client_order_id_prefix,
            'position': str(self.position),
            'create_time': self.create_time,
            'status': self.status.name
        }

    @property
    def summary(self) -> typing.Dict[str, typing.Any]:
        return self.state

    @property
    def client_order_id_prefix(self) -> str:
        return baseconv.base58.encode(id(self))

    def generate_order_id(self) -> str:
        return next(self._order_id_sequence)

    @dataclasses.dataclass
    class OrderFillSummary:
        qty: Decimal
        average_price: float
        commissions: typing.Dict[str, Decimal]

        @classmethod
        def from_binance_fills(cls, binance_fills: typing.Sequence[dict]):
            cum_qty = Decimal(0)
            cum_partial_prices = 0.0
            commissions = collections.Counter()

            if not binance_fills:
                raise ValueError('List of fills is empty')
            for fill in binance_fills:
                qty = Decimal(fill['qty'])
                cum_qty += qty
                cum_partial_prices += (float(qty) * float(fill['price']))
                commissions.update({
                    fill['commissionAsset']: Decimal(fill['commission'])
                })          

            return cls(
                cum_qty, cum_partial_prices / float(cum_qty), dict(commissions)
            )

    def on_order_response(self, response: dict):
        'Called with the order execution info returned by Binance'
        order_id = response.get('clientOrderId')
        orig_qty = Decimal(response['origQty'])
        exec_qty = Decimal(response.get('executedQty', 0))
        transact_time = response.get('transactTime', 0)
        side = response.get('side')
        status = response.get('status', 'UNKNOWN')
        if exec_qty == 0:
            logger.info(
            'Order %s to %s %s not filled at t=%d. status: %s',
            order_id, side, orig_qty, transact_time, status)
            return

        fill_summary = self.OrderFillSummary.from_binance_fills(
            response['fills']
        )
        if fill_summary.qty != exec_qty:
            logger.warning(
                'Inconsistent exec quantity %s ≠ total fills %s',
                exec_qty, fill_summary.qty)

        if orig_qty == exec_qty:
            if status.upper() != 'FILLED':
                raise ValueError(
                    f'Order {order_id} appears fully filled but status is {status}')
            logger.info(
                'Order %s %s %s filled. Got price %f at t=%d',
                order_id,
                side,
                exec_qty,
                fill_summary.average_price,
                transact_time
            )
            strategy_journal.update_strategy_position(strategy_id=self.client_order_id_prefix, state=self.state , new_position=exec_qty, side=side)
        else:
            logger.info(
                'Order %s %s %s/%s partly filled. Got price %f at t=%d. status: %s',
                order_id,
                side,
                exec_qty,
                orig_qty,
                fill_summary.average_price,
                transact_time,
                status
            )
            strategy_journal.update_strategy_position(strategy_id=self.client_order_id_prefix, state=self.state , new_position=exec_qty, side=side)

        # TODO: Calculate average fill price and commission.
        position_increment_sign = {
            'BUY': 1,
            'SELL': -1
        }[side]
        self.position += position_increment_sign * exec_qty
        return
