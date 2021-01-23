import logging
import collections
import asyncio
import typing

import binance


logger = logging.getLogger(__name__)


class CandleLiveTimeline:
    def __init__(self, symbol):
        self.symbol = symbol.lower()
        self.interval = '1m'
        self.candles_min_required = 60
        self.current_candle = None
        self.candle_timeline = []
        self.binance_client = None

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
            if not self.is_ready:
                asyncio.create_task(self._supplement_earlier_candles())

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
    def latest_candles(self) -> typing.List[dict]:
        return self.candle_timeline[-self.candles_min_required:]

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
            self.candle_timeline[:0] = [
                dict(collections.ChainMap(
                    dict(zip(column_names, c)),
                    {'first_trade_id': None, 'last_trade_id': None},
                    earliest_available))
                for c in candles if c[0] < earliest_available['start_time']
            ]

        return


class MarketFeed:
    def __init__(self, symbols: typing.Sequence[str]):
        self.candle_timelines = {
            s: CandleLiveTimeline(s) for s in symbols
        }

    @property
    def symbols(self) -> typing.Set[str]:
        return set(self.candle_timelines)

    def register_for_candles(
        self,
        client: binance.Client
    ) -> None:
        for timeline in self.candle_timelines.values():
            timeline.binance_client = client
            client.events.register_event(
                timeline.on_kline,
                timeline.kline_stream_name
            )

    def get_latest_candles_for_symbol(self, symbol: str):
        timeline = self.candle_timelines[symbol]
        return timeline.latest_candles
