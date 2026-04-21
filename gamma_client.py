from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from models import Market


class GammaClient:
    """
    Lightweight public market metadata fetcher.

    Gamma response shapes can drift, so parsing is intentionally defensive.
    """

    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def list_markets(self, limit: int = 200) -> list[dict[str, Any]]:
        candidates = [
            f"{self.BASE_URL}/markets?limit={limit}",
            f"{self.BASE_URL}/events?limit={limit}",
        ]
        for url in candidates:
            try:
                resp = requests.get(url, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    for key in ("markets", "data", "events"):
                        value = data.get(key)
                        if isinstance(value, list):
                            return value
            except Exception:
                continue
        return []

    def parse_fast_markets(self, rows: list[dict[str, Any]]) -> list[Market]:
        markets: list[Market] = []
        for row in rows:
            market = self._parse_market_row(row)
            if market is not None:
                markets.append(market)
        return markets

    def _parse_market_row(self, row: dict[str, Any]) -> Market | None:
        question = str(row.get("question") or row.get("title") or "").strip()
        slug = str(row.get("slug") or row.get("ticker") or "").strip()
        market_id = str(row.get("id") or row.get("conditionId") or slug or question).strip()

        text = f"{question} {slug}".lower()
        asset = ""
        if "bitcoin" in text or "btc" in text:
            asset = "BTC"
        elif "ethereum" in text or "eth" in text:
            asset = "ETH"
        else:
            return None

        duration_minutes = 0
        if "5 minute" in text or "5m" in text or "5 minutes" in text:
            duration_minutes = 5
        elif "15 minute" in text or "15m" in text or "15 minutes" in text:
            duration_minutes = 15
        else:
            return None

        end_time_raw = (
            row.get("endDate")
            or row.get("end_time")
            or row.get("endTimestamp")
            or row.get("end")
        )
        end_time = self._parse_datetime(end_time_raw)
        if end_time is None:
            return None

        active = bool(row.get("active", True))
        if end_time <= datetime.now(timezone.utc):
            active = False

        yes_token_id, no_token_id = self._extract_token_ids(row)
        if not yes_token_id or not no_token_id:
            return None

        return Market(
            market_id=market_id,
            question=question or slug,
            slug=slug,
            asset=asset,
            duration_minutes=duration_minutes,
            yes_token_id=yes_token_id,
            no_token_id=no_token_id,
            end_time=end_time,
            active=active,
        )

    def _extract_token_ids(self, row: dict[str, Any]) -> tuple[str | None, str | None]:
        # Common Gamma shapes vary; try several patterns.
        tokens = row.get("tokens")
        if isinstance(tokens, list) and len(tokens) >= 2:
            first = tokens[0] or {}
            second = tokens[1] or {}
            t1 = str(first.get("token_id") or first.get("tokenId") or first.get("id") or "").strip()
            t2 = str(second.get("token_id") or second.get("tokenId") or second.get("id") or "").strip()
            if t1 and t2:
                return t1, t2

        outcomes = row.get("outcomes")
        clob_ids = row.get("clobTokenIds")

        if isinstance(clob_ids, list) and len(clob_ids) >= 2:
            return str(clob_ids[0]), str(clob_ids[1])

        if isinstance(clob_ids, str):
            parts = [p.strip().strip('"') for p in clob_ids.strip("[]").split(",") if p.strip()]
            if len(parts) >= 2:
                return parts[0], parts[1]

        if isinstance(outcomes, list) and len(outcomes) >= 2:
            # Not always enough to get token IDs.
            pass

        return None, None

    def _parse_datetime(self, raw: Any) -> datetime | None:
        if raw is None:
            return None

        if isinstance(raw, (int, float)):
            try:
                return datetime.fromtimestamp(float(raw), tz=timezone.utc)
            except Exception:
                return None

        text = str(raw).strip()
        if not text:
            return None

        candidates = [
            text,
            text.replace("Z", "+00:00"),
        ]

        for candidate in candidates:
            try:
                dt = datetime.fromisoformat(candidate)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue

        return None
