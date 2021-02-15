import logging
from decimal import Decimal
import strategy_base
MAX_QUANTITY = 1000

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
        self.take_profit_price = Decimal(advice.get('SL1'))
        self.stop_loss_price = Decimal(advice.get('TP1'))


    def validate_external_command(self):
        if (not self.entry_quantity > 0):
                       logger.error(
                "Ignored trade-plan, non positive quantaty: %s",
                repr(self.entry_quantity))
        if (not self.entry_quantity < MAX_QUANTITY):
                       logger.error(
                "Ignored trade-plan, quantaty bellow max: %s",
                repr(self.entry_quantity))


    def plan_trade(self, candle: dict):
        # To log messages use e.g. logger.info( ... )
        # If not trade is to be exdcuted, return None
        # Else, return an object as-per the example below
        self.validate_external_command()
        return strategy_base.TradePlanAtUnspecifiedPrice(
            symbol=candle['symbol'],
            entry_quantity=self.entry_quantity,
            take_profit_price=self.take_profit_price,
            stop_loss_price=self.stop_loss_price
        )
