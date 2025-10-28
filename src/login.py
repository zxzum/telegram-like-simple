"""
Interactive Telegram login script
Use this to create/update session file
"""

import asyncio
import logging
from telethon import TelegramClient
from src import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Interactive login"""
    try:
        logger.info("=" * 70)
        logger.info("🔐 TELEGRAM LOGIN")
        logger.info("=" * 70)
        logger.info(f"Session file: sessions/{config.SESSION_NAME}")
        logger.info(f"API ID: {config.API_ID}")
        logger.info("")

        client = TelegramClient(
            f'sessions/{config.SESSION_NAME}',
            config.API_ID,
            config.API_HASH
        )

        logger.info("📱 Connecting to Telegram...")
        await client.connect()
        logger.info("✅ Connected to Telegram!")

        logger.info("")
        logger.info("🔑 Starting authentication...")
        logger.info("📝 Enter your phone number (with country code, e.g., +1234567890)")

        # This will prompt for phone and code
        await client.start(phone=config.PHONE_NUMBER)

        logger.info("✅ Authentication successful!")

        # Get user info
        me = await client.get_me()
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"✅ LOGGED IN AS:")
        logger.info(f"   👤 Name: {me.first_name} {me.last_name or ''}")
        logger.info(f"   📱 Username: @{me.username}")
        logger.info(f"   🆔 User ID: {me.id}")
        logger.info("=" * 70)
        logger.info("")
        logger.info("✅ Session file saved to: sessions/userbot")
        logger.info("✅ You can now run: make run")
        logger.info("")

        await client.disconnect()

    except Exception as e:
        logger.error(f"❌ Login failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    asyncio.run(main())