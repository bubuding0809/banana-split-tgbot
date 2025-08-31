"""
Banana Split Telegram Bot - Main Entry Point
"""

import logging
from bot_config import BotConfiguration

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the Banana Split Telegram bot.

    Creates and runs the bot using the BotConfiguration class.
    """
    try:
        bot_config = BotConfiguration()
        bot_config.run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
