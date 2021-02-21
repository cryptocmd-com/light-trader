import decimal
import typing
import asyncio
import logging
import abc

import binance
import strategy_base
import trade_plan


logger = logging.getLogger(__name__)


# FIXME: Sort asynchronous execution so that this class
# starts new tasks that send the commands to the exchange
class ImmediateOrderExecutor(abc.ABC):
    def __init__(self, client: binance.Client):
        self.client = client

    @property
    @abc.abstractmethod
    def symbol_traded(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def generate_order_id(self) -> typing.Generator[str, None, None]:
        raise NotImplementedError

    async def send_immediate_order(
        self,
        side: str,
        quantity: decimal.Decimal
    ) -> dict:
        new_client_order_id = next(self.generate_order_id())
        try:
            response = await self.client.create_order(
                self.symbol_traded,
                getattr(binance.Side, side).value,
                binance.OrderType.MARKET.value,
                quantity=quantity,
                new_client_order_id=new_client_order_id
            )
            return response

        except binance.errors.BinanceError:
            # TODO: Check whether it's safe to assume that the order
            # was rejected and not executed.
            logger.exception(
                'Binance rejected order %s to %s %s %s',
                new_client_order_id, side, quantity, self.symbol_traded)

        return {
            'clientOrderId': new_client_order_id,
            'origQty': quantity,
            'executedQty': 0,
            'status': 'FAILED'
        }


class StrategyPriceSwing(
    strategy_base.StrategyBase,
    ImmediateOrderExecutor
):
    def __init__(
        self,
        client: binance.Client,
        trade_plan: trade_plan.TradePlanAtTargetPrice
    ):
        strategy_base.StrategyBase.__init__(self)
        ImmediateOrderExecutor.__init__(self, client)
        self.plan = trade_plan
        if self.plan.action != 'BUY':
            raise ValueError(
                f'Short trade-plan is not supported: {trade_plan}')

    @property
    def take_profit_price(self) -> decimal.Decimal:
        return self.plan.take_profit_price

    @property
    def stop_loss_price(self) -> decimal.Decimal:
        return self.stop_loss_price

    # TODO: Support trading multiple symbols
    @property
    def symbol_traded(self) -> str:
        return self.plan.symbol

    @property
    def symbols_monitored(self) -> typing.Set[str]:
        return {self.symbol_traded}

    def on_candle(self, candle: dict):
        future = None
        current_price = decimal.Decimal(candle['close_price'])
        if (self.position == 0 and
                current_price <= self.plan.entry_price):
            future = self._open_position()
        elif self.position != 0 and not (
            self.stop_loss_price < current_price < self.take_profit_price
        ):
            future = self._close_position()

        if future is not None:
            # TODO: Retain the task object
            asyncio.create_task(future)

    async def _open_position(self):
        response = await self.send_immediate_order(
            'BUY', self.plan.quantity)
        self.on_order_response(response)

    async def _close_position(self):
        response = await self.send_immediate_order('SELL', self.position)
        self.on_order_response(response)

