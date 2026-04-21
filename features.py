from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict, deque
from typing import Optional

from models import Market, OrderBookSnapshot


@dataclass
class FeatureVector:
    market_id: str
    token_id: str
    mid: Optional[float]
    spread: Optional[float]
    spread_cents: Optional[float]
    imbalance: float
    depth_total_3: float
    short_return: Optional[float]
    seconds_to_expiry: int


class MidHistoryStore:
    def __init__(self, max_points: int = 200):
        self._data: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=max_points))

    def add(self, token_id: str, mid: Optional[float]) -> None:
        if mid is not None:
            self._data[token_id].append(mid)

    def short_return(self, token_id: str, lookback_points: int = 5) -> Optional[float]:
        series = self._data.get(token_id)
        if not series or len(series) <= lookback_points:
            return None
        old = series[-(lookback_points + 1)]
        new = series[-1]
        if old == 0:
            return None
        return (new - old) / old


def compute_imbalance(book: OrderBookSnapshot) -> float:
    total = book.depth_bid_3 + book.depth_ask_3
    if total <= 0:
        return 0.0
    return (book.depth_bid_3 - book.depth_ask_3) / total


def build_feature_vector(
    market: Market,
    token_id: str,
    book: OrderBookSnapshot,
    short_return: Optional[float],
    seconds_to_expiry: int,
) -> FeatureVector:
    spread_cents = None if book.spread is None else book.spread * 100.0
    return FeatureVector(
        market_id=market.market_id,
        token_id=token_id,
        mid=book.mid,
        spread=book.spread,
        spread_cents=spread_cents,
        imbalance=compute_imbalance(book),
        depth_total_3=book.depth_bid_3 + book.depth_ask_3,
        short_return=short_return,
        seconds_to_expiry=seconds_to_expiry,
    )
