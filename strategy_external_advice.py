from decimal import Decimal
import strategy_base


class StrategyExternalAdvice(strategy_base.StrategyBase):
    'A stategy created by external advice'
    def __init__(
        self,
        executor: strategy_base.TradePlanExecutor,
        advice: dict
    ):
        super().__init__(executor)
        self.entry_quantity = Decimal('0.01')
        self.take_profit_price = Decimal(advice.get('TP1', '35000'))
        self.stop_loss_price = Decimal(advice.get('SL1', '28000'))

    def plan_trade(self, candle: dict):
        return strategy_base.TradePlanAtUnspecifiedPrice(
            symbol=candle['symbol'],
            entry_quantity=self.entry_quantity,
            take_profit_price=self.take_profit_price,
            stop_loss_price=self.stop_loss_price
        )
