import decimal
import typing
import logging

import binance

import strategy_base
import trade_plan
import Immediate_order_executor


logger = logging.getLogger(__name__)


class StrategyPriceSwing(
    strategy_base.StrategyBase,
    Immediate_order_executor.ImmediateOrderExecutor
):
    '''StrategyPriceSwing: Base-class for strategies that attempt to
    gain from a price swing, from an entry price to a target price.
    Note: currently only long trades are supported.
    '''

    def __init__(
        self,
        client: binance.Client,
        trade_plan: trade_plan.TradePlanAtTargetPrice
    ):
        strategy_base.StrategyBase.__init__(self)
        Immediate_order_executor.ImmediateOrderExecutor.__init__(self, client)
        self.plan = trade_plan
        if self.plan.action != 'BUY':
            raise ValueError(
                f'Short trade-plan is not supported: {trade_plan}')

    @property
    def take_profit_price(self) -> decimal.Decimal:
        return self.plan.take_profit_price

    @property
    def stop_loss_price(self) -> decimal.Decimal:
        return self.plan.stop_loss_price

    # TODO: Support trading multiple symbols
    @property
    def symbol_traded(self) -> str:
        return self.plan.symbol

    @property
    def symbols_monitored(self) -> typing.Set[str]:
        return {self.symbol_traded}

    async def on_candle(self, candle: dict) -> None:
        current_price = decimal.Decimal(candle['close_price'])
        if (self.position == 0 and
                current_price <= self.plan.entry_price):
            await self._open_position()
        elif self.position != 0 and not (
            self.stop_loss_price < current_price < self.take_profit_price
        ):
            await self._close_position()
        else:
            logger.debug(
                'Strategy %s: Nothing to do for current_price %s',
                self.client_order_id_prefix, current_price
            )

    async def _open_position(self):
        response = await self.send_immediate_order(
            'BUY', self.plan.entry_quantity)
        logger.debug(
            'Strategy %s opened position: BUY %s',
            self.client_order_id_prefix, self.plan.entry_quantity)
        self.on_order_response(response)

    async def _close_position(self):
        position_reduction = self.position
        response = await self.send_immediate_order('SELL', position_reduction)
        logger.debug(
            'Strategy %s closed position: SELL %s',
            self.client_order_id_prefix, position_reduction)
        self.on_order_response(response)
