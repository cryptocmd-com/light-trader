import logging
import typing
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
        try:
            symbol = str(advice['symbol'])
            for name, value in advice.items():
                if isinstance(value, float):
                    raise TypeError(
                        f'Value of {name} is given as a float {value}. Use integer or string instead')
            stop_loss_price = Decimal(advice['SL1'])
            take_profit_price = Decimal(advice['TP1'])
            entry_price = Decimal(advice['entry'])
            entry_quantity = Decimal(advice['quantity'])
            
        except KeyError as ex:
            raise ValueError(f'Missing mandatory field: {ex.args[0]}') from ex
        except TypeError:
            logger.exception('A value could not be converted to decimal')
            raise

        plan = trade_plan.TradePlanAtTargetPrice(
            symbol,
            entry_quantity=entry_quantity,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            entry_price=entry_price
        )

        super().__init__(client, plan)
        self.set_status('ACTIVE')
    
    @property
    def state(self) -> typing.Dict[str, typing.Any]:
        state_dict = super().state
        state_dict.update(
        {
            "SL1" : str(self.stop_loss_price),
            "TP1" : str(self.take_profit_price),
            "symbol" : str(self.plan.symbol),
            "entry" :  str(self.plan.entry_price),
            "quantity" : str(self.plan.entry_quantity)
        })
        return state_dict



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
