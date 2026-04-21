import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _get_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)).strip())


def _get_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)).strip())


def _get_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    gamma_base_url: str = "https://gamma-api.polymarket.com"
    clob_base_url: str = "https://clob.polymarket.com"

    assets: tuple[str, ...] = ("BTC", "ETH")
    durations: tuple[str, ...] = ("5m", "15m")

    loop_interval_seconds: int = 3
    market_refresh_seconds: int = 20
    trade_lookback_seconds: int = 120

    min_seconds_left_5m: int = 45
    min_seconds_left_15m: int = 120

    max_spread_cents: float = 6.0
    min_depth_contracts: float = 50.0

    paper_starting_cash: float = 1000.0
    paper_order_size: float = 25.0
    paper_max_open_positions: int = 1

    enable_btc: bool = True
    enable_eth: bool = True

    log_level: str = "INFO"


def load_settings() -> Settings:
    assets = tuple(_get_list("BOT_ASSETS", "BTC,ETH"))
    durations = tuple(_get_list("BOT_DURATIONS", "5m,15m"))

    return Settings(
        assets=assets,
        durations=durations,
        loop_interval_seconds=_get_int("LOOP_INTERVAL_SECONDS", 3),
        market_refresh_seconds=_get_int("MARKET_REFRESH_SECONDS", 20),
        trade_lookback_seconds=_get_int("TRADE_LOOKBACK_SECONDS", 120),
        min_seconds_left_5m=_get_int("MIN_SECONDS_LEFT_5M", 45),
        min_seconds_left_15m=_get_int("MIN_SECONDS_LEFT_15M", 120),
        max_spread_cents=_get_float("MAX_SPREAD_CENTS", 6.0),
        min_depth_contracts=_get_float("MIN_DEPTH_CONTRACTS", 50.0),
        paper_starting_cash=_get_float("PAPER_STARTING_CASH", 1000.0),
        paper_order_size=_get_float("PAPER_ORDER_SIZE", 25.0),
        paper_max_open_positions=_get_int("PAPER_MAX_OPEN_POSITIONS", 1),
        enable_btc=_get_bool("ENABLE_BTC", True),
        enable_eth=_get_bool("ENABLE_ETH", True),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
    )
