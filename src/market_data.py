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


COINCAP_API = "https://api.coincap.io/v2"

PAIR_TO_COINCAP = {
    "BTC/USD": "bitcoin",
    "ETH/USD": "ethereum",
    "SOL/USD": "solana",
}

HEADERS = {"User-Agent": "claude-auto-trader/0.1.0"}


def _fetch_from_coingecko(pair: str, coin_id: str) -> MarketSnapshot | None:
    """Try fetching from CoinGecko first."""
    try:
        resp = requests.get(
            f"{COINGECKO_API}/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
            },
            headers=HEADERS,
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
        logger.warning("CoinGecko failed for %s: %s, trying fallback...", pair, e)
        return None


def _fetch_from_coincap(pair: str, coin_id: str) -> MarketSnapshot | None:
    """Fallback: fetch from CoinCap API."""
    try:
        resp = requests.get(
            f"{COINCAP_API}/assets/{coin_id}",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        asset = resp.json()["data"]

        return MarketSnapshot(
            pair=pair,
            price=float(asset["priceUsd"]),
            volume_24h=float(asset["volumeUsd24Hr"]),
            change_24h_pct=float(asset["changePercent24Hr"]),
            market_cap=float(asset["marketCapUsd"]),
            timestamp=datetime.now(timezone.utc),
        )
    except (requests.RequestException, KeyError, ValueError) as e:
        logger.error("CoinCap also failed for %s: %s", pair, e)
        return None


def fetch_market_data(pair: str) -> MarketSnapshot | None:
    """Fetch current market data for a trading pair. Tries CoinGecko then CoinCap."""
    coingecko_id = PAIR_TO_COINGECKO.get(pair)
    coincap_id = PAIR_TO_COINCAP.get(pair)

    if not coingecko_id:
        logger.error("Unsupported trading pair: %s", pair)
        return None

    result = _fetch_from_coingecko(pair, coingecko_id)
    if result:
        return result

    if coincap_id:
        return _fetch_from_coincap(pair, coincap_id)

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
