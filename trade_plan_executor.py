import abc
from decimal import Decimal

import binance

import trade_plan


class TradeEventHandler(abc.ABC):
    @abc.abstractmethod
    def on_take_profit_executed(tp):
        raise NotImplementedError

    @abc.abstractmethod
    def on_stop_loss_executed(sl):
        raise NotImplementedError


class TradePlanExecutor:
    def __init__(self, client: binance.Client):
        self.client = client

    # TODO: Subscribe to execution reports and somehow adjust the strategy's position

    async def execute_plan_at_market_price(
        self,
        callback_handler: TradeEventHandler,
        plan: trade_plan.TradePlanAtUnspecifiedPrice
    ) -> Decimal:
        'Execute a trade plan using a market order, and return the position increment'

        # Send commands to enter a position and then set the take-profit + stop-loss.
        return Decimal(0)
