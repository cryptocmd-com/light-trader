import logging
from decimal import Decimal

import binance
import trade_plan
import strategy_price_swing
MAX_QUANTITY = 1000

logger = logging.getLogger(__name__)


class StrategyExternalAdvice(strategy_price_swing.StrategyPriceSwing):
    'A stategy created by external advice'
    def __init__(
        self,
        client: binance.Client,
        advice: dict
    ):
        # TODO: Check arguments. If they're not satisfactory raise ValueError
        stop_loss_price = Decimal(advice.get('SL1'))
        take_profit_price = Decimal(advice.get('TP1'))
        entry_price = (take_profit_price + stop_loss_price) / 2   # Use real value!
        plan = trade_plan.TradePlanAtTargetPrice(
            advice['symbol'],
            entry_quantity=Decimal('0.01'),
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            entry_price=entry_price
        )

        super().__init__(client, plan)


'''
    def validate_external_command(self):
        if (not self.entry_quantity > 0):
                       logger.error(
                "Ignored trade-plan, non positive quantaty: %s",
                repr(self.entry_quantity))
        if (not self.entry_quantity < MAX_QUANTITY):
                       logger.error(
                "Ignored trade-plan, quantaty bellow max: %s",
                repr(self.entry_quantity))
'''
