# Polycryptotrader
# Polymarket Paper Bot

Paper-only bot for short-duration Polymarket crypto markets.

## Scope
- BTC / ETH only
- 5 minute / 15 minute markets only
- paper trading only
- read-only market data

## Files
- `config.py` - environment + runtime settings
- `models.py` - dataclasses
- `gamma_client.py` - market discovery
- `clob_client.py` - orderbook/trade reads
- `market_discovery.py` - filters + ranking
- `features.py` - market features
- `signals.py` - 5m / 15m signal logic
- `paper_broker.py` - fake execution + pnl
- `dashboard.py` - terminal output
- `run_paper_bot.py` - main loop

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run_paper_bot.py
