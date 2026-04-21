from __future__ import annotations

from rich.console import Console
from rich.table import Table

from features import FeatureVector
from models import BotState, Market, SignalDecision


console = Console()


def render_dashboard(
    market: Market | None,
    yes_features: FeatureVector | None,
    no_features: FeatureVector | None,
    signal: SignalDecision | None,
    state: BotState,
    unrealized_pnl: float,
) -> None:
    console.clear()

    title = "Polymarket Paper Bot"
    console.rule(title)

    summary = Table(title="Bot State")
    summary.add_column("Field")
    summary.add_column("Value")

    summary.add_row("Cash", f"{state.cash:.2f}")
    summary.add_row("Realized PnL", f"{state.realized_pnl:.2f}")
    summary.add_row("Unrealized PnL", f"{unrealized_pnl:.2f}")
    summary.add_row("Open Positions", str(len(state.positions)))
    summary.add_row("Trades", str(len(state.trades)))
    summary.add_row("Last Note", state.last_note or "-")
    console.print(summary)

    if market is None:
        console.print("[yellow]No eligible market found.[/yellow]")
        return

    market_tbl = Table(title="Selected Market")
    market_tbl.add_column("Field")
    market_tbl.add_column("Value")
    market_tbl.add_row("Question", market.question)
    market_tbl.add_row("Asset", market.asset)
    market_tbl.add_row("Duration", f"{market.duration_minutes}m")
    market_tbl.add_row("Ends", market.end_time.isoformat())
    console.print(market_tbl)

    feat_tbl = Table(title="YES / NO Features")
    feat_tbl.add_column("Metric")
    feat_tbl.add_column("YES")
    feat_tbl.add_column("NO")

    def fmt(x):
        if x is None:
            return "-"
        if isinstance(x, float):
            return f"{x:.4f}"
        return str(x)

    if yes_features and no_features:
        feat_tbl.add_row("Mid", fmt(yes_features.mid), fmt(no_features.mid))
        feat_tbl.add_row("Spread cents", fmt(yes_features.spread_cents), fmt(no_features.spread_cents))
        feat_tbl.add_row("Imbalance", fmt(yes_features.imbalance), fmt(no_features.imbalance))
        feat_tbl.add_row("Depth total (3)", fmt(yes_features.depth_total_3), fmt(no_features.depth_total_3))
        feat_tbl.add_row("Short return", fmt(yes_features.short_return), fmt(no_features.short_return))
        feat_tbl.add_row("Seconds to expiry", fmt(yes_features.seconds_to_expiry), fmt(no_features.seconds_to_expiry))
    console.print(feat_tbl)

    sig_tbl = Table(title="Signal")
    sig_tbl.add_column("Field")
    sig_tbl.add_column("Value")
    if signal:
        sig_tbl.add_row("Action", signal.action)
        sig_tbl.add_row("Confidence", f"{signal.confidence:.2f}")
        sig_tbl.add_row("Fair Price", "-" if signal.fair_price is None else f"{signal.fair_price:.4f}")
        sig_tbl.add_row("Max Entry Price", "-" if signal.max_entry_price is None else f"{signal.max_entry_price:.4f}")
        sig_tbl.add_row("Reason", signal.reason)
        sig_tbl.add_row("Time Stop", str(signal.time_stop_seconds))
    console.print(sig_tbl)

    pos_tbl = Table(title="Positions")
    pos_tbl.add_column("Side")
    pos_tbl.add_column("Question")
    pos_tbl.add_column("Entry")
    pos_tbl.add_column("Size")
    pos_tbl.add_column("Entry Time")
    if state.positions:
        for pos in state.positions:
            pos_tbl.add_row(
                pos.side,
                pos.question[:60],
                f"{pos.entry_price:.4f}",
                f"{pos.size:.2f}",
                pos.entry_time.isoformat(),
            )
    else:
        pos_tbl.add_row("-", "-", "-", "-", "-")
    console.print(pos_tbl)
