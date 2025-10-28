"""
Simple Telegram Userbot for Auto-Reactions in Topics
Based on Telethon library
"""

import asyncio
import logging
import sys
from src.userbot import SimpleUserBot
from src import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the userbot"""
    try:
        logger.info("🚀 Starting Telegram Userbot...")

        bot = SimpleUserBot()
        logger.info("✅ UserBot instance created")

        # Start the bot
        await bot.start()
        logger.info("✅ UserBot started and listening...")

    except KeyboardInterrupt:
        logger.info("❌ Bot stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot terminated")
        sys.exit(0)