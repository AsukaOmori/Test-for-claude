"""Configuration management for claude-auto-trader."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TradingConfig:
    """Trading configuration loaded from environment variables."""

    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"))
    trading_pair: str = field(default_factory=lambda: os.getenv("TRADING_PAIR", "BTC/USD"))
    max_position_size: float = field(
        default_factory=lambda: float(os.getenv("MAX_POSITION_SIZE", "0.01"))
    )
    risk_limit_pct: float = field(
        default_factory=lambda: float(os.getenv("RISK_LIMIT_PCT", "2.0"))
    )
    check_interval_sec: int = field(
        default_factory=lambda: int(os.getenv("CHECK_INTERVAL_SEC", "60"))
    )
    dry_run: bool = field(
        default_factory=lambda: os.getenv("DRY_RUN", "true").lower() == "true"
    )
    exchange_api_key: str = field(default_factory=lambda: os.getenv("EXCHANGE_API_KEY", ""))
    exchange_api_secret: str = field(default_factory=lambda: os.getenv("EXCHANGE_API_SECRET", ""))

    def validate(self) -> list[str]:
        """Return a list of validation errors, empty if config is valid."""
        errors = []
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")
        if self.max_position_size <= 0:
            errors.append("MAX_POSITION_SIZE must be positive")
        if not 0 < self.risk_limit_pct <= 100:
            errors.append("RISK_LIMIT_PCT must be between 0 and 100")
        return errors
