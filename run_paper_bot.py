from __future__ import annotations

import time
from datetime import datetime, timezone

from clob_client import ClobClient
from config import load_settings
from dashboard import render_dashboard
from features import MidHistoryStore, build_feature_vector
from gamma_client import GammaClient
from market_discovery import discover_markets, rank_markets, seconds_to_expiry
from paper_broker import PaperBroker
from signals import build_signal


def main() -> None:
    settings = load_settings()
    gamma = GammaClient()
    clob = ClobClient()
    broker = PaperBroker(settings)
    mids = MidHistoryStore()

    markets = []
    last_market_refresh = 0.0

    while True:
        now_ts = time.time()

        if now_ts - last_market_refresh >= settings.market_refresh_seconds:
            markets = rank_markets(discover_markets(settings, gamma))
            last_market_refresh = now_ts

        selected_market = markets[0] if markets else None

        if selected_market is None:
            render_dashboard(
                market=None,
                yes_features=None,
                no_features=None,
                signal=None,
                state=broker.state,
                unrealized_pnl=0.0,
            )
            time.sleep(settings.loop_seconds)
            continue

        yes_book = clob.get_orderbook(selected_market.yes_token_id)
        no_book = clob.get_orderbook(selected_market.no_token_id)

        if yes_book is None or no_book is None:
            broker.state.last_note = "orderbook_unavailable"
            render_dashboard(
                market=selected_market,
                yes_features=None,
                no_features=None,
                signal=None,
                state=broker.state,
                unrealized_pnl=0.0,
            )
            time.sleep(settings.loop_seconds)
            continue

        mids.add(selected_market.yes_token_id, yes_book.mid)
        mids.add(selected_market.no_token_id, no_book.mid)

        secs = seconds_to_expiry(selected_market)

        yes_features = build_feature_vector(
            market=selected_market,
            token_id=selected_market.yes_token_id,
            book=yes_book,
            short_return=mids.short_return(selected_market.yes_token_id, lookback_points=3),
            seconds_to_expiry=secs,
        )

        no_features = build_feature_vector(
            market=selected_market,
            token_id=selected_market.no_token_id,
            book=no_book,
            short_return=mids.short_return(selected_market.no_token_id, lookback_points=3),
            seconds_to_expiry=secs,
        )

        # Simple side chooser:
        # build the main signal off YES side features, but allow NO if its own signal is stronger.
        yes_signal = build_signal(selected_market.duration_minutes, yes_features)
        no_signal = build_signal(selected_market.duration_minutes, no_features)

        chosen_signal = yes_signal
        if no_signal.action == "BUY_YES":
            # BUY_YES on NO token logically means BUY_NO on market
            chosen_signal = no_signal
            chosen_signal.action = "BUY_NO"
        elif no_signal.confidence > yes_signal.confidence:
            chosen_signal = no_signal

        broker.maybe_exit_positions(
            market=selected_market,
            yes_mid=yes_book.mid,
            no_mid=no_book.mid,
        )

        broker.maybe_open_position(
            market=selected_market,
            signal=chosen_signal,
            yes_mid=yes_book.mid,
            no_mid=no_book.mid,
        )

        unrealized = broker.unrealized_pnl(
            market=selected_market,
            yes_mid=yes_book.mid,
            no_mid=no_book.mid,
        )

        render_dashboard(
            market=selected_market,
            yes_features=yes_features,
            no_features=no_features,
            signal=chosen_signal,
            state=broker.state,
            unrealized_pnl=unrealized,
        )

        time.sleep(settings.loop_seconds)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
