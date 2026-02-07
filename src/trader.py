"""Core trading engine that orchestrates the trading loop."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from anthropic import Anthropic

from src.config import TradingConfig
from src.market_data import fetch_market_data
from src.strategy import Signal, TradeDecision, analyze_market

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    timestamp: datetime
    pair: str
    signal: Signal
    price: float
    size: float
    confidence: float
    reasoning: str


@dataclass
class Trader:
    """Main trading engine."""

    config: TradingConfig
    client: Anthropic = field(init=False)
    current_position: float = 0.0
    trade_history: list[TradeRecord] = field(default_factory=list)

    def __post_init__(self):
        self.client = Anthropic(api_key=self.config.anthropic_api_key)

    def run_cycle(self) -> TradeDecision | None:
        """Execute one analysis-and-trade cycle."""
        logger.info("Fetching market data for %s...", self.config.trading_pair)
        snapshot = fetch_market_data(self.config.trading_pair)
        if snapshot is None:
            logger.warning("Could not fetch market data, skipping cycle.")
            return None

        logger.info(
            "Current price: $%,.2f (24h: %+.2f%%)",
            snapshot.price,
            snapshot.change_24h_pct,
        )

        logger.info("Analyzing market with Claude...")
        decision = analyze_market(
            self.client, self.config, snapshot, self.current_position
        )
        if decision is None:
            logger.warning("Could not get analysis, skipping cycle.")
            return None

        logger.info(
            "Signal: %s (confidence: %.1f%%) - %s",
            decision.signal.value,
            decision.confidence * 100,
            decision.reasoning,
        )

        self._execute(decision, snapshot.price)
        return decision

    def _execute(self, decision: TradeDecision, price: float):
        """Execute a trade decision (or simulate in dry-run mode)."""
        if decision.signal == Signal.HOLD:
            logger.info("Holding current position.")
            return

        size = self.config.max_position_size * decision.suggested_size

        if decision.signal == Signal.BUY:
            action = "BUY"
            self.current_position += size
        else:
            action = "SELL"
            self.current_position -= size

        record = TradeRecord(
            timestamp=datetime.now(timezone.utc),
            pair=self.config.trading_pair,
            signal=decision.signal,
            price=price,
            size=size,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
        )
        self.trade_history.append(record)

        if self.config.dry_run:
            logger.info(
                "[DRY RUN] %s %.6f %s @ $%,.2f | Position: %.6f",
                action, size, self.config.trading_pair, price, self.current_position,
            )
        else:
            logger.info(
                "EXECUTING %s %.6f %s @ $%,.2f | Position: %.6f",
                action, size, self.config.trading_pair, price, self.current_position,
            )
            self._place_order(decision.signal, size, price)

    def _place_order(self, signal: Signal, size: float, price: float):
        """Place an actual order on the exchange. Stub for real implementation."""
        logger.warning(
            "Live trading not yet implemented. Would %s %.6f @ $%,.2f",
            signal.value, size, price,
        )

    def print_summary(self):
        """Print a summary of trading activity."""
        total_trades = len(self.trade_history)
        buys = sum(1 for t in self.trade_history if t.signal == Signal.BUY)
        sells = sum(1 for t in self.trade_history if t.signal == Signal.SELL)
        logger.info(
            "Session summary: %d trades (%d buys, %d sells) | Position: %.6f",
            total_trades, buys, sells, self.current_position,
        )
