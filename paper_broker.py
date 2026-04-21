from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from config import Settings
from models import BotState, Market, PaperPosition, PaperTrade, SignalDecision


class PaperBroker:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.state = BotState(cash=settings.starting_cash)

    def has_open_position(self) -> bool:
        return len(self.state.positions) > 0

    def can_open_new_position(self) -> bool:
        return len(self.state.positions) < self.settings.max_open_positions

    def maybe_open_position(
        self,
        market: Market,
        signal: SignalDecision,
        yes_mid: Optional[float],
        no_mid: Optional[float],
    ) -> None:
        if signal.action not in {"BUY_YES", "BUY_NO"}:
            return

        if not self.can_open_new_position():
            self.state.last_note = "max_open_positions_reached"
            return

        if signal.action == "BUY_YES":
            token_id = market.yes_token_id
            side = "YES"
            price = yes_mid
        else:
            token_id = market.no_token_id
            side = "NO"
            price = no_mid

        if price is None:
            self.state.last_note = "no_price_for_entry"
            return

        notional = min(self.settings.max_position_notional, self.state.cash)
        if notional <= 0:
            self.state.last_note = "no_cash"
            return

        size = round(notional, 2)  # simple: 1 contract ~= $1 notional here
        cost = round(size * price, 2)

        if cost > self.state.cash:
            size = round(self.state.cash / max(price, 0.01), 2)
            cost = round(size * price, 2)

        if size <= 0:
            self.state.last_note = "size_zero"
            return

        position = PaperPosition(
            market_id=market.market_id,
            token_id=token_id,
            side=side,
            entry_price=price,
            size=size,
            entry_time=datetime.now(timezone.utc),
            duration_minutes=market.duration_minutes,
            question=market.question,
        )
        self.state.positions.append(position)
        self.state.cash -= cost
        self.state.last_note = f"opened_{side.lower()}"

        self.state.trades.append(
            PaperTrade(
                ts=datetime.now(timezone.utc),
                market_id=market.market_id,
                token_id=token_id,
                side=side,
                action="OPEN",
                price=price,
                size=size,
                note=signal.reason,
            )
        )

    def maybe_exit_positions(
        self,
        market: Market,
        yes_mid: Optional[float],
        no_mid: Optional[float],
    ) -> None:
        now = datetime.now(timezone.utc)
        remaining = []

        for pos in self.state.positions:
            if pos.market_id != market.market_id:
                remaining.append(pos)
                continue

            max_hold = timedelta(seconds=90 if pos.duration_minutes == 5 else 240)
            should_exit = (now - pos.entry_time) >= max_hold or now >= market.end_time

            if not should_exit:
                remaining.append(pos)
                continue

            exit_price = yes_mid if pos.side == "YES" else no_mid
            if exit_price is None:
                remaining.append(pos)
                continue

            proceeds = round(pos.size * exit_price, 2)
            entry_cost = round(pos.size * pos.entry_price, 2)
            pnl = round(proceeds - entry_cost, 2)

            self.state.cash += proceeds
            self.state.realized_pnl += pnl
            self.state.last_note = f"closed_{pos.side.lower()}"

            self.state.trades.append(
                PaperTrade(
                    ts=now,
                    market_id=pos.market_id,
                    token_id=pos.token_id,
                    side=pos.side,
                    action="CLOSE",
                    price=exit_price,
                    size=pos.size,
                    pnl=pnl,
                    note="time_exit",
                )
            )

        self.state.positions = remaining

    def unrealized_pnl(
        self,
        market: Market,
        yes_mid: Optional[float],
        no_mid: Optional[float],
    ) -> float:
        pnl = 0.0
        for pos in self.state.positions:
            if pos.market_id != market.market_id:
                continue
            mark = yes_mid if pos.side == "YES" else no_mid
            if mark is None:
                continue
            pnl += (mark - pos.entry_price) * pos.size
        return round(pnl, 2)
