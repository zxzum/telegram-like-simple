"""
Telegram Auto-Reaction System
- Regular Bot: Controls userbot (enable/disable via commands)
- Userbot: Adds reactions when enabled
"""

import asyncio
import logging
import sys
import os
from src.userbot import SimpleUserBot
from src.bot import RegularBot, BotController
from src import config

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Start both regular bot and userbot in parallel"""
    try:
        # Create controller for managing userbot state
        controller = BotController()

        # Get bot token from environment
        bot_token = os.getenv('BOT_TOKEN', '')
        if not bot_token:
            raise ValueError("❌ BOT_TOKEN not set in .env file!")

        logger.info("🚀 Starting Telegram Bot System...")
        logger.info("=" * 60)

        # Create bots
        userbot = SimpleUserBot(controller=controller)
        regular_bot = RegularBot(token=bot_token, controller=controller)

        # Run both bots in parallel
        logger.info("📌 Running userbot and regular bot concurrently...")

        await asyncio.gather(
            userbot.start(),  # Userbot listens for messages and adds reactions
            regular_bot.start()  # Regular bot listens for control commands
        )

    except KeyboardInterrupt:
        logger.info("🛑 Bot system stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())