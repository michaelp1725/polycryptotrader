from __future__ import annotations

from datetime import datetime, timezone

from config import Settings
from models import Market
from gamma_client import GammaClient


def seconds_to_expiry(market: Market) -> int:
    now = datetime.now(timezone.utc)
    return max(0, int((market.end_time - now).total_seconds()))


def market_allowed_by_settings(market: Market, settings: Settings) -> bool:
    if market.asset == "BTC" and not settings.enable_btc:
        return False
    if market.asset == "ETH" and not settings.enable_eth:
        return False

    if market.asset not in settings.assets:
        return False

    label = f"{market.duration_minutes}m"
    if label not in settings.durations:
        return False

    if not market.active:
        return False

    return True


def market_has_enough_time_left(market: Market, settings: Settings) -> bool:
    secs = seconds_to_expiry(market)
    if market.duration_minutes == 5:
        return secs >= settings.min_time_left_5m_seconds
    if market.duration_minutes == 15:
        return secs >= settings.min_time_left_15m_seconds
    return False


def discover_markets(settings: Settings, gamma_client: GammaClient) -> list[Market]:
    rows = gamma_client.list_markets()
    markets = gamma_client.parse_fast_markets(rows)
    markets = [m for m in markets if market_allowed_by_settings(m, settings)]
    markets = [m for m in markets if market_has_enough_time_left(m, settings)]
    return markets


def rank_markets(markets: list[Market]) -> list[Market]:
    # Simpler rule: prefer 5m first, then nearest expiry.
    return sorted(
        markets,
        key=lambda m: (
            m.duration_minutes,
            seconds_to_expiry(m),
            m.asset,
        ),
    )
