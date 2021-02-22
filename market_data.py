import abc
import logging
import collections
import asyncio
import typing

import binance


logger = logging.getLogger(__name__)


class MarketFeedEventHandler(abc.ABC):
    @abc.abstractmethod
    async def on_candle(self, candle: dict):
        raise NotImplementedError


class CandleLiveTimeline:
    def __init__(
            self,
            symbol: str,
            event_handlers: typing.Iterable[MarketFeedEventHandler] = ()
        ):
        self.symbol = symbol.lower()
        self.interval = '1m'
        self.candles_min_required = 1
        self.current_candle = None
        self.candle_timeline = collections.deque(
            maxlen=self.candles_min_required)
        self.binance_client = None
        self.event_handlers: typing.List[MarketFeedEventHandler] = list(
            event_handlers)

    def add_event_handler(self, new_handler: MarketFeedEventHandler) -> None:
        for handler in self.event_handlers:
            if handler is new_handler:
                break
        else:
            self.event_handlers.append(new_handler)

    @property
    def kline_stream_name(self) -> str:
        return f'{self.symbol}@kline_{self.interval}'

    @property
    def is_ready(self) -> bool:
        return len(self.candle_timeline) >= self.candles_min_required

    def on_kline(self, event: binance.events.KlineWrapper):
        if not event.event_type.lower().startswith('kline'):
            raise TypeError(f'Unexpected event type: {event.event_type}')

        self.current_candle = event
        if self.current_candle.kline_closed:
            self.candle_timeline.append(
                self._extract_kline_fields(self.current_candle))

            if self.is_ready:
                on_candle_futures = [
                    subscriber.on_candle(self.candle_timeline[-1])
                    for subscriber in self.event_handlers]
                future = asyncio.wait(on_candle_futures)
            else:
                future = self._supplement_earlier_candles()
            asyncio.create_task(future)

    @staticmethod
    def _extract_kline_fields(event: binance.events.KlineWrapper):
        prefix = 'kline_'
        prefix_len = len(prefix)
        return {
            k[prefix_len:]: v
            for k, v in event.__dict__.items()
            if k.startswith(prefix)
        }

    @property
    def latest_candles(self) -> typing.Tuple[dict]:
        return tuple(self.candle_timeline)

    async def _supplement_earlier_candles(self):
        n_missing = self.candles_min_required - len(self.candle_timeline)
        if n_missing > 0:
            # TODO: Generalize this for other intervals.
            earliest_available = self.candle_timeline[0]
            assert (earliest_available['interval'] ==
                    binance.definitions.Interval.ONE_MINUTE.value)
            request_from_time = (
                earliest_available['start_time'] -
                n_missing * 60 * 1000)
            logging.info(
                "Requesting %d earlier candles from time %d",
                n_missing, request_from_time)
            candles = await self.binance_client.fetch_klines(
                earliest_available['symbol'],
                earliest_available['interval'],
                request_from_time,
                limit=n_missing
            )

            column_names = (
                'start_time',
                'open_price',
                'high_price',
                'low_price',
                'close_price',
                'base_asset_volume',
                'close_time',
                'quote_asset_volume',
                'trades_number',
                'taker_buy_base_asset_volume',
                'taker_buy_quote_asset_volume'
            )
            self.candle_timeline.extendleft(
                dict(collections.ChainMap(
                    dict(zip(column_names, c)),
                    {
                        'first_trade_id': None,
                        'last_trade_id': None,
                        'symbol': earliest_available['symbol']
                    },
                    earliest_available))
                for c in reversed(candles) if c[0] < earliest_available['start_time']
            )

        return


class MarketFeed:
    def __init__(self, client: binance.Client):
        self.client = client
        self.candle_timelines: typing.Dict[str, CandleLiveTimeline] = {}
        self.market_events_listener_task = None

    @property
    def symbols(self) -> typing.Set[str]:
        return set(self.candle_timelines)

    def register_handler(
        self,
        symbol: str,
        handler: MarketFeedEventHandler
    ) -> None:
        if symbol not in self.candle_timelines:
            if symbol not in self.client.symbols:
                raise ValueError(
                    f'Symbol not supported by the exchange: {symbol}')
            timeline = CandleLiveTimeline(symbol, (handler,))
            timeline.binance_client = self.client
            self.candle_timelines[symbol] = timeline
            self.client.events.register_event(
                timeline.on_kline,
                timeline.kline_stream_name
            )
            if self.market_events_listener_task is not None:
                self.market_events_listener_task.cancel()
            self.market_events_listener_task = asyncio.create_task(
                self.client.start_market_events_listener())
        else:
            self.candle_timelines[symbol].add_event_handler(handler)

    def get_latest_candles_for_symbol(self, symbol: str):
        timeline = self.candle_timelines[symbol]
        return timeline.latest_candles
