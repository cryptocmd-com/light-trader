import logging
from decimal import Decimal
import strategy_base


logger = logging.getLogger(__name__)


class StrategyExternalAdvice(strategy_base.StrategyBase):
    'A stategy created by external advice'
    def __init__(
        self,
        executor: strategy_base.TradePlanExecutor,
        advice: dict
    ):
        # TODO: Check arguments. If they're not satisfactory raise ValueError
        super().__init__(executor)
        self.entry_quantity = Decimal('0.01')
        self.take_profit_price = Decimal(advice.get('TP1', '35000'))
        self.stop_loss_price = Decimal(advice.get('SL1', '28000'))

    def plan_trade(self, candle: dict):
        # To log messages use e.g. logger.info( ... )

        # If no trade is to be executed, return None
        # Else, return an object as-per the example below
        return strategy_base.TradePlanAtUnspecifiedPrice(
            symbol=candle['symbol'],
            entry_quantity=self.entry_quantity,
            take_profit_price=self.take_profit_price,
            stop_loss_price=self.stop_loss_price
        )
