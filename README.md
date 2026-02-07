# Claude Auto Trader

Automated trading assistant powered by Claude AI. Fetches real-time market data, uses Claude to analyze trends and generate trading signals, and executes trades (or simulates them in dry-run mode).

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd claude-auto-trader

# 2. Create .env file and add your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# 3. Install dependencies
pip install -e .

# 4. Run the trader
python -m src.main
```

## Configuration

All settings are controlled via environment variables (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model for analysis |
| `TRADING_PAIR` | `BTC/USD` | Trading pair (`BTC/USD`, `ETH/USD`, `SOL/USD`) |
| `MAX_POSITION_SIZE` | `0.01` | Max position size in base currency |
| `RISK_LIMIT_PCT` | `2.0` | Risk limit as % of portfolio |
| `CHECK_INTERVAL_SEC` | `60` | Seconds between market checks |
| `DRY_RUN` | `true` | Simulate trades without executing |

## Architecture

```
src/
├── main.py          # Entry point and trading loop
├── config.py        # Configuration from environment
├── market_data.py   # Market data fetching (CoinGecko)
├── strategy.py      # Claude-powered trading analysis
└── trader.py        # Trade execution engine
```

## How It Works

1. **Fetch** real-time price data from CoinGecko
2. **Analyze** market conditions using Claude
3. **Decide** BUY / SELL / HOLD with confidence score
4. **Execute** the trade (or log it in dry-run mode)
5. **Repeat** at the configured interval
