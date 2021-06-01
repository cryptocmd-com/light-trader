import decimal
import typing
import logging

import binance
from strategy_journal import strategy_journal

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

    @property
    def summary(self) -> typing.Dict[str, typing.Any]:
        result = super().state
        result['symbol_traded'] = self.symbol_traded
        return result

    async def on_candle(self, candle: dict) -> None:
        current_price = decimal.Decimal(candle['close_price'])
        if (self.position == 0 and
                current_price <= self.plan.entry_price and
                self.status == self.Status.ACTIVE):
            await self._open_position()
            logger.debug(
                'Strategy %s opened position at price %s: BUY %s %s',
                self.client_order_id_prefix,
                current_price,
                self.plan.entry_quantity,
                self.symbol_traded
            )
        elif self.position != 0 and (
            not (self.stop_loss_price < current_price < self.take_profit_price) or self.status == self.Status.STOPPED
        ):
            await self._close_position()
            if (self.position == 0 and self.status != self.Status.STOPPED):
                self.status = self.Status.COMPLETE
                strategy_journal.update_strategy_status(strategy_id=self.state['strategy_id'], state=self.state, new_status='COMPLETE')
            logger.debug(
                'Strategy %s closing position of %s %s at price %s',
                self.client_order_id_prefix,
                self.position,
                self.symbol_traded,
                current_price
            )
        else:
            logger.debug(
                'Strategy %s: Nothing to do for current_price %s',
                self.client_order_id_prefix, current_price
            )

    async def _open_position(self):
        response = await self.send_immediate_order(
            'BUY', self.plan.entry_quantity)
        self.on_order_response(response)

    async def _close_position(self):
        position_reduction = self.position
        side = 'BUY' if position_reduction < 0 else 'SELL'
        response = await self.send_immediate_order(side, position_reduction)
        self.on_order_response(response)
