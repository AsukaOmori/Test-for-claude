"""Entry point for claude-auto-trader."""

import logging
import signal
import sys
import time

from src.config import TradingConfig
from src.trader import Trader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info("Received signal %d, shutting down gracefully...", signum)
    _running = False


def main():
    global _running

    logger.info("=== Claude Auto Trader ===")

    config = TradingConfig()
    errors = config.validate()
    if errors:
        for err in errors:
            logger.error("Config error: %s", err)
        sys.exit(1)

    mode = "DRY RUN" if config.dry_run else "LIVE"
    logger.info("Mode: %s | Pair: %s | Interval: %ds", mode, config.trading_pair, config.check_interval_sec)

    trader = Trader(config=config)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("Starting trading loop (Ctrl+C to stop)...")

    try:
        while _running:
            trader.run_cycle()
            if _running:
                logger.info("Next check in %d seconds...", config.check_interval_sec)
                # Sleep in small increments so we can respond to signals quickly
                for _ in range(config.check_interval_sec):
                    if not _running:
                        break
                    time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        trader.print_summary()
        logger.info("Trader stopped.")


if __name__ == "__main__":
    main()
