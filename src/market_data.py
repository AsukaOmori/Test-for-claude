"""Market data fetching module."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

COINGECKO_API = "https://api.coingecko.com/api/v3"

PAIR_TO_COINGECKO = {
    "BTC/USD": "bitcoin",
    "ETH/USD": "ethereum",
    "SOL/USD": "solana",
}


@dataclass
class MarketSnapshot:
    """A point-in-time snapshot of market data."""

    pair: str
    price: float
    volume_24h: float
    change_24h_pct: float
    market_cap: float
    timestamp: datetime


def fetch_market_data(pair: str) -> MarketSnapshot | None:
    """Fetch current market data for a trading pair from CoinGecko."""
    coin_id = PAIR_TO_COINGECKO.get(pair)
    if not coin_id:
        logger.error("Unsupported trading pair: %s", pair)
        return None

    try:
        resp = requests.get(
            f"{COINGECKO_API}/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        market = data["market_data"]
        return MarketSnapshot(
            pair=pair,
            price=market["current_price"]["usd"],
            volume_24h=market["total_volume"]["usd"],
            change_24h_pct=market["price_change_percentage_24h"],
            market_cap=market["market_cap"]["usd"],
            timestamp=datetime.now(timezone.utc),
        )
    except requests.RequestException as e:
        logger.error("Failed to fetch market data for %s: %s", pair, e)
        return None


def format_market_summary(snapshot: MarketSnapshot) -> str:
    """Format a market snapshot into a human-readable summary for Claude."""
    return (
        f"Market Data for {snapshot.pair} at {snapshot.timestamp.isoformat()}:\n"
        f"  Price: ${snapshot.price:,.2f}\n"
        f"  24h Change: {snapshot.change_24h_pct:+.2f}%\n"
        f"  24h Volume: ${snapshot.volume_24h:,.0f}\n"
        f"  Market Cap: ${snapshot.market_cap:,.0f}"
    )
