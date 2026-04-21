from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Market:
    market_id: str
    question: str
    slug: str
    asset: str
    duration_minutes: int
    yes_token_id: str
    no_token_id: str
    end_time: datetime
    active: bool = True


@dataclass
class OrderBookSnapshot:
    token_id: str
    best_bid: Optional[float]
    best_ask: Optional[float]
    bid_size: float
    ask_size: float
    depth_bid_3: float
    depth_ask_3: float
    ts: datetime

    @property
    def mid(self) -> Optional[float]:
        if self.best_bid is None or self.best_ask is None:
            return None
        return (self.best_bid + self.best_ask) / 2.0

    @property
    def spread(self) -> Optional[float]:
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid


@dataclass
class SignalDecision:
    action: str  # BUY_YES, BUY_NO, EXIT, HOLD
    confidence: float
    fair_price: Optional[float]
    max_entry_price: Optional[float]
    reason: str
    time_stop_seconds: int


@dataclass
class PaperPosition:
    market_id: str
    token_id: str
    side: str  # YES or NO
    entry_price: float
    size: float
    entry_time: datetime
    duration_minutes: int
    question: str


@dataclass
class PaperTrade:
    ts: datetime
    market_id: str
    token_id: str
    side: str
    action: str
    price: float
    size: float
    pnl: float = 0.0
    note: str = ""


@dataclass
class BotState:
    cash: float
    realized_pnl: float = 0.0
    positions: list[PaperPosition] = field(default_factory=list)
    trades: list[PaperTrade] = field(default_factory=list)
    last_note: str = ""
