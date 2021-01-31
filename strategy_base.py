import typing
import asyncio
import logging
import abc
from decimal import Decimal

from trade_plan import TradePlanAtUnspecifiedPrice
from trade_plan_executor import TradePlanExecutor, TradeEventHandler
from market_data import MarketFeedEventHandler

logger = logging.getLogger(__name__)


class StrategyBase(
    TradeEventHandler,
    MarketFeedEventHandler
):
    def __init__(self, executor: TradePlanExecutor):
        self.executor = executor
        self.position = Decimal(0)
        # TODO: Determine maximum position

    @abc.abstractmethod
    def plan_trade(sel, candle: dict) -> typing.Optional[
            TradePlanAtUnspecifiedPrice]:
        raise NotImplementedError

    def on_candle(self, candle: dict):
        plan = self.plan_trade(candle)
        if plan is None:
            return

        # FIXME: There's a potential race here, as the previous task
        # might still be in progress, and we could enter into a
        # larger position than intended. We should probably
        # at least check that the last submitted task is complete.
        asyncio.create_task(self._execute_trade_plan(plan))

    async def _execute_trade_plan(
        self,
        trade_plan: TradePlanAtUnspecifiedPrice
    ) -> bool:

        if self.position:
            # TODO: Compare the position to a maximum value
            # Also: handle the case when we have to flip directly
            # between long and short.
            logger.debug(
                "Ignored trade-plan because of existing position: %s",
                repr(trade_plan))
            return False

        position_increment = await self.executor.execute_plan_at_market_price(
            self, trade_plan)
        self.position += position_increment
        logger.info("Executed trade %s", repr(trade_plan))
        return True

    # FIXME: Change the position based on the amount executed
    def on_take_profit_executed(tp):
        pass

    def on_stop_loss_executed(sl):
        pass
