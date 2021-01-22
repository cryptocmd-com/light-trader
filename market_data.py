import logging
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

    @property
    def kline_stream_name(self) -> str:
        return f'{self.symbol}@kline_{self.interval}'

    @property
    def is_ready(self) -> bool:
        return len(self.candle_timeline) >= self.candles_min_required

    def on_kline(self, event: binance.events.KlineWrapper):
        self.current_candle = event
        if self.current_candle.kline_closed:
            self.candle_timeline.append(self.current_candle)


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
            client.events.register_event(
                timeline.on_kline,
                timeline.kline_stream_name
            )

