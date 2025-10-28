"""
Simple Telegram Userbot - Auto Reaction Logic
- Controlled by regular bot (enable/disable)
- When enabled: Add ❤️ reaction with 0.3s delay
- When disabled: Do nothing
"""

import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji, PeerUser
from src import config
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
REACTION = '❤️'  # Heart emoji reaction
REACTION_DELAY = 0.1  # 0.3 second delay
MESSAGE_INTERVAL = 2  # Flood control


class SimpleUserBot:
    def __init__(self, controller=None):
        logger.info("📦 Initializing UserBot...")

        self.client = TelegramClient(
            f'sessions/{config.SESSION_NAME}',
            config.API_ID,
            config.API_HASH
        )
        self.last_action_time = 0
        self.my_user_id = None
        self.controller = controller  # Reference to bot controller
        self.active = True  # Initial state

    async def check_rate_limit(self):
        """Flood control"""
        current_time = asyncio.get_event_loop().time()

        if current_time - self.last_action_time < MESSAGE_INTERVAL:
            wait_time = MESSAGE_INTERVAL - (current_time - self.last_action_time)
            await asyncio.sleep(wait_time)

        self.last_action_time = asyncio.get_event_loop().time()

    async def add_reaction(self, chat_id: int, message_id: int) -> bool:
        """Add heart reaction to message"""
        try:
            await self.check_rate_limit()
            reaction_obj = ReactionEmoji(emoticon=REACTION)

            await self.client(SendReactionRequest(
                peer=chat_id,
                msg_id=message_id,
                reaction=[reaction_obj]
            ))

            logger.info(f"✅ Added {REACTION} to msg {message_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding reaction: {e}")
            return False

    async def handle_new_message(self, event):
        """Handle new message"""
        try:
            # Check if userbot is enabled via controller
            if self.controller and not self.controller.is_enabled():
                logger.debug("⏸️  Userbot is disabled, ignoring message")
                return

            message = event.message

            # Ignore service messages
            if message.action:
                return

            # Ignore own messages
            if config.IGNORE_OWN_MESSAGES and message.from_id:
                if isinstance(message.from_id, PeerUser):
                    if message.from_id.user_id == self.my_user_id:
                        return

            logger.info(f"📨 New message {message.id}: {message.text[:40] if message.text else 'No text'}")

            # Delay before reaction (0.3 seconds)
            await asyncio.sleep(REACTION_DELAY)

            # Add heart reaction
            await self.add_reaction(event.chat_id, message.id)

        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")

    async def start(self):
        """Start userbot"""
        try:
            logger.info("🔐 Connecting to Telegram...")
            await self.client.start()

            me = await self.client.get_me()
            if me is None:
                raise RuntimeError("Authentication failed")

            self.my_user_id = me.id

            logger.info("=" * 60)
            logger.info(f"✅ USERBOT STARTED")
            logger.info(f"   👤 User: {me.username or me.first_name} (ID: {self.my_user_id})")
            logger.info(f"   💬 Chat: {config.CHAT_ID}")
            logger.info(f"   📌 Topic: {config.TOPIC_ID}")
            logger.info(f"   😊 Reaction: {REACTION}")
            logger.info(f"   ⏱️  Delay: {REACTION_DELAY}s")
            logger.info("=" * 60)
            logger.info("👂 Listening for messages...\n")

            @self.client.on(events.NewMessage(chats=config.CHAT_ID))
            async def message_handler(event):
                message = event.message

                # Check topic filter
                if config.TOPIC_ID is not None and config.TOPIC_ID > 0:
                    if not message.reply_to:
                        return

                    is_forum = getattr(message.reply_to, 'forum_topic', False)
                    if not is_forum:
                        return

                    topic_msg_id = getattr(message.reply_to, 'reply_to_msg_id', None)
                    if topic_msg_id != config.TOPIC_ID:
                        return

                await self.handle_new_message(event)

            await self.client.run_until_disconnected()

        except Exception as e:
            logger.error(f"❌ ERROR: {e}")
            raise