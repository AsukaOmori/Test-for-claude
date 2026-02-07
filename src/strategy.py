"""Trading strategy module using Claude for analysis."""

import json
import logging
from dataclasses import dataclass
from enum import Enum

from anthropic import Anthropic

from src.config import TradingConfig
from src.market_data import MarketSnapshot, format_market_summary

logger = logging.getLogger(__name__)


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeDecision:
    signal: Signal
    confidence: float  # 0.0 - 1.0
    reasoning: str
    suggested_size: float  # fraction of max position


ANALYSIS_PROMPT = """\
You are a trading analysis assistant. Analyze the following market data and provide a trading signal.

{market_summary}

Current position: {position_info}
Risk limit: {risk_limit_pct}% of portfolio

Respond ONLY with valid JSON in this exact format:
{{
    "signal": "BUY" | "SELL" | "HOLD",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<brief explanation>",
    "suggested_size": <float 0.0-1.0, fraction of max position>
}}
"""


def analyze_market(
    client: Anthropic,
    config: TradingConfig,
    snapshot: MarketSnapshot,
    current_position: float,
) -> TradeDecision | None:
    """Use Claude to analyze market data and produce a trading signal."""
    position_info = (
        f"{current_position} units" if current_position != 0 else "No open position"
    )

    prompt = ANALYSIS_PROMPT.format(
        market_summary=format_market_summary(snapshot),
        position_info=position_info,
        risk_limit_pct=config.risk_limit_pct,
    )

    try:
        response = client.messages.create(
            model=config.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        result = json.loads(text)
        return TradeDecision(
            signal=Signal(result["signal"]),
            confidence=float(result["confidence"]),
            reasoning=result["reasoning"],
            suggested_size=float(result["suggested_size"]),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error("Failed to parse Claude's response: %s", e)
        return None
    except Exception as e:
        logger.error("Claude API error: %s", e)
        return None
