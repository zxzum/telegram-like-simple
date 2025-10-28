"""
Telegram Auto-Reaction Userbot
"""

import asyncio
import logging
import sys
from src.userbot import SimpleUserBot
from src import config

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Start the userbot"""
    try:
        bot = SimpleUserBot()
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())