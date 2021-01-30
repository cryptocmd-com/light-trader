from dataclasses import dataclass, field
from decimal import Decimal

@dataclass
class TradePlanAtUnspecifiedPrice:
    ''' A plan for a trade, comprising the position size, the
    take-profit and stop-loss points. No specific entry price is specified.
    '''

    symbol: str
    entry_quantity: Decimal
    take_profit_price: Decimal
    stop_loss_price: Decimal
    action: str = field(init=False, repr=False)

    def __post_init__(self):
        if self.take_profit_price > self.stop_loss_price:
            action = 'BUY'
        elif self.take_profit_price < self.stop_loss_price:
            action = 'SELL'
        else:
            raise ValueError(
                'Invalid trade plan: take-profit and stop-loss prices must differ')


@dataclass
class TradePlanAtTargetPrice(TradePlanAtUnspecifiedPrice):
    ''' A plan for a trade, comprising a specific entry price,
    the position size, the take-profit and stop-loss points
    '''
    entry_price: Decimal

    def __post_init__(self):
        super().__post_init__()
        low = min(self.take_profit_price, self.stop_loss_price)
        high = max(self.take_profit_price, self.stop_loss_price)
        if not low < self.entry_price < high:
            raise ValueError(
                'The entry price is not between the take-profit and stop-loss prices.')
