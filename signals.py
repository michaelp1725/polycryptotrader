from __future__ import annotations

from models import SignalDecision
from features import FeatureVector


def build_5m_signal(features: FeatureVector) -> SignalDecision:
    if features.mid is None:
        return SignalDecision("HOLD", 0.0, None, None, "no_mid", 20)

    if features.spread_cents is None or features.spread_cents > 4:
        return SignalDecision("HOLD", 0.0, features.mid, None, "spread_too_wide", 20)

    if features.depth_total_3 < 50:
        return SignalDecision("HOLD", 0.0, features.mid, None, "depth_too_thin", 20)

    if features.seconds_to_expiry < 45:
        return SignalDecision("HOLD", 0.0, features.mid, None, "too_close_to_expiry", 10)

    short_return = features.short_return or 0.0

    if short_return > 0.003 and features.imbalance > 0.12:
        fair = min(0.99, (features.mid or 0.5) + 0.01)
        return SignalDecision(
            action="BUY_YES",
            confidence=0.72,
            fair_price=fair,
            max_entry_price=fair,
            reason="5m_momentum_up",
            time_stop_seconds=90,
        )

    if short_return < -0.003 and features.imbalance < -0.12:
        fair = max(0.01, (features.mid or 0.5) - 0.01)
        return SignalDecision(
            action="BUY_NO",
            confidence=0.72,
            fair_price=fair,
            max_entry_price=1.0 - fair,
            reason="5m_momentum_down",
            time_stop_seconds=90,
        )

    return SignalDecision("HOLD", 0.0, features.mid, None, "no_5m_edge", 20)


def build_15m_signal(features: FeatureVector) -> SignalDecision:
    if features.mid is None:
        return SignalDecision("HOLD", 0.0, None, None, "no_mid", 45)

    if features.spread_cents is None or features.spread_cents > 4:
        return SignalDecision("HOLD", 0.0, features.mid, None, "spread_too_wide", 45)

    if features.depth_total_3 < 50:
        return SignalDecision("HOLD", 0.0, features.mid, None, "depth_too_thin", 45)

    if features.seconds_to_expiry < 180:
        return SignalDecision("HOLD", 0.0, features.mid, None, "too_close_to_expiry", 30)

    short_return = features.short_return or 0.0

    if short_return > 0.002 and features.imbalance > 0.08:
        fair = min(0.99, (features.mid or 0.5) + 0.008)
        return SignalDecision(
            action="BUY_YES",
            confidence=0.66,
            fair_price=fair,
            max_entry_price=fair,
            reason="15m_trend_up",
            time_stop_seconds=240,
        )

    if short_return < -0.002 and features.imbalance < -0.08:
        fair = max(0.01, (features.mid or 0.5) - 0.008)
        return SignalDecision(
            action="BUY_NO",
            confidence=0.66,
            fair_price=fair,
            max_entry_price=1.0 - fair,
            reason="15m_trend_down",
            time_stop_seconds=240,
        )

    return SignalDecision("HOLD", 0.0, features.mid, None, "no_15m_edge", 45)


def build_signal(duration_minutes: int, features: FeatureVector) -> SignalDecision:
    if duration_minutes == 5:
        return build_5m_signal(features)
    return build_15m_signal(features)
