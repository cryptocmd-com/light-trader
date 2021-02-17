import abc
import logging
import json
from decimal import Decimal

import binance

import trade_plan


logger = logging.getLogger(__name__)


class TradeEventHandler(abc.ABC):
    @abc.abstractmethod
    def on_take_profit_executed(tp):
        raise NotImplementedError

    @abc.abstractmethod
    def on_stop_loss_executed(sl):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def client_order_id_prefix(self) -> str:
        raise NotImplementedError


class TradePlanExecutor:
    def __init__(self, client: binance.Client):
        self.client = client
        self.order_counter = 0

    # TODO: Subscribe to execution reports and somehow adjust the strategy's position

    async def execute_plan_at_market_price(
        self,
        callback_handler: TradeEventHandler,
        plan: trade_plan.TradePlanAtUnspecifiedPrice
    ) -> Decimal:
        'Execute a trade plan using a market order, and return the position increment'

        order_counter = self._get_next_order_counter()
        new_client_order_id = (
            f'{callback_handler.client_order_id_prefix}_{order_counter:06}')
        try:
            response = await self.client.create_order(
                plan.symbol,
                getattr(binance.Side, plan.action).value,
                binance.OrderType.MARKET.value,
                quantity=str(plan.entry_quantity),
                new_client_order_id=new_client_order_id
            )

            if response.get('status') != 'FILLED':
                logger.error('Market order %s was not filled: %s',
                            new_client_order_id, json.dumps(response))
            elif response.get('origQty') != response.get('executedQty'):
                logger.warning('Market order %s was only partially filled: %s',
                            new_client_order_id, json.dumps(response))
            else:
                logger.info('Executing plan %s and got response %s',
                            repr(plan), json.dumps(response))

            total_fill = Decimal(response.get('executedQty'))
            if total_fill != 0:
                await self._send_closing_order(plan, response)
        except binance.errors.BinanceError:
            logger.exception(
                'Sending order %s failed', new_client_order_id)

        return {'BUY': 1, 'SELL': -1}[response.get('side')] * total_fill
        # TODO: Capture the fills in the format:
        # [{'price': '7000.02000000', 'qty': '0.01000000',
        # 'commission': '0.00000000', 'commissionAsset': 'BTC', 'tradeId': 2987}]

    def _get_next_order_counter(self) -> int:
        self.order_counter += 1
        return self.order_counter

    async def _send_closing_order(
        self,
        plan: trade_plan.TradePlanAtUnspecifiedPrice,
        entry_fill: dict
    ) -> dict:
        '''Send an order to close the position that was opened by the entry_order
        "entry_fill"
        '''

        strategy_id = entry_fill['clientOrderId'].split('_')[0]
        oco_client_order_id = f'{strategy_id}_{self._get_next_order_counter()}'
        # stop_client_order_id = f'{strategy_id}_{self._get_next_order_counter()}'

        closing_side = {
            'BUY': 'SELL',
            'SELL': 'BUY'
        }[entry_fill['side']]
        response = await self.client.create_oco(
            entry_fill['symbol'],
            closing_side,
            entry_fill['executedQty'],
            plan.take_profit_price,
            plan.stop_loss_price,
            list_client_order_id=oco_client_order_id
        )

        logger.info('Sent OCO: %s', json.dumps(response))
        return response
