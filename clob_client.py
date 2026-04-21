from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from models import OrderBookSnapshot


class ClobClient:
    """
    Public read-only client for Polymarket CLOB.
    """

    BASE_URL = "https://clob.polymarket.com"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_orderbook(self, token_id: str) -> OrderBookSnapshot | None:
        candidates = [
            f"{self.BASE_URL}/book?token_id={token_id}",
            f"{self.BASE_URL}/book?tokenId={token_id}",
        ]

        for url in candidates:
            try:
                resp = requests.get(url, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                snapshot = self._parse_book(token_id, data)
                if snapshot:
                    return snapshot
            except Exception:
                continue

        return None

    def _parse_book(self, token_id: str, data: dict[str, Any]) -> OrderBookSnapshot | None:
        bids = data.get("bids") or []
        asks = data.get("asks") or []

        best_bid, bid_size, depth_bid_3 = self._extract_side(bids, reverse=True)
        best_ask, ask_size, depth_ask_3 = self._extract_side(asks, reverse=False)

        if best_bid is None and best_ask is None:
            return None

        return OrderBookSnapshot(
            token_id=token_id,
            best_bid=best_bid,
            best_ask=best_ask,
            bid_size=bid_size,
            ask_size=ask_size,
            depth_bid_3=depth_bid_3,
            depth_ask_3=depth_ask_3,
            ts=datetime.now(timezone.utc),
        )

    def _extract_side(self, levels: list[dict[str, Any]], reverse: bool) -> tuple[float | None, float, float]:
        parsed: list[tuple[float, float]] = []

        for row in levels:
            try:
                price = float(row.get("price"))
                size = float(row.get("size"))
                parsed.append((price, size))
            except Exception:
                continue

        if not parsed:
            return None, 0.0, 0.0

        parsed.sort(key=lambda x: x[0], reverse=reverse)
        best_price, best_size = parsed[0]
        depth_3 = sum(size for _, size in parsed[:3])
        return best_price, best_size, depth_3
