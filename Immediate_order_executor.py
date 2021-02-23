import decimal
import logging
import abc

import binance


logger = logging.getLogger(__name__)


class ImmediateOrderExecutor(abc.ABC):
    '''ImmediateOrderExecutor: send orders that execute completely
    immediately, such as market orders, and process the response
    '''
    def __init__(self, client: binance.Client):
        self.client = client

    @property
    @abc.abstractmethod
    def symbol_traded(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def generate_order_id(self) -> str:
        raise NotImplementedError

    async def send_immediate_order(
        self,
        side: str,
        quantity: decimal.Decimal
    ) -> dict:
        new_client_order_id = self.generate_order_id()
        try:
            response = await self.client.create_order(
                self.symbol_traded,
                getattr(binance.Side, side).value,
                binance.OrderType.MARKET.value,
                quantity=quantity,
                response_type=binance.definitions.ResponseType.FULL.value,
                new_client_order_id=new_client_order_id
            )
            return response

        except binance.errors.BinanceError:
            # TODO: Check whether it's safe to assume that the order
            # was rejected and not executed.
            logger.exception(
                'Binance rejected order %s to %s %s %s',
                new_client_order_id, side, quantity, self.symbol_traded)

        return {
            'clientOrderId': new_client_order_id,
            'origQty': quantity,
            'executedQty': 0,
            'status': 'FAILED'
        }
