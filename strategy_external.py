from decimal import Decimal
import strategy_base


class StrategyExternal(strategy_base.StrategyBase):
    'A mock strategy which returns a fixed value'
    def plan_trade(sel, candle: dict):
        return strategy_base.TradePlanAtUnspecifiedPrice(
            symbol='BTCUSDT',
            entry_quantity=Decimal('0.01'),
            take_profit_price=Decimal('35000'),
            stop_loss_price=Decimal('28000')
        )
