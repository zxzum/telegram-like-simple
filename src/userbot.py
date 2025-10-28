"""
Simple Telegram Userbot - Auto Reaction Logic
- Post reaction after 0.2-1 sec delay
- Remove reaction if only ours after 20 sec
- Monitor for 5 minutes after removal
- Switch to popular reaction if 2+ people use it
"""

import asyncio
import random
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
REACTIONS = ['👍', '❤️']
INITIAL_DELAY = (0.2, 1.0)
CHECK_REMOVE_DELAY = 20
MONITOR_AFTER_REMOVE = 300
MESSAGE_INTERVAL = 2
SWITCH_THRESHOLD = 2


class MessageTracker:
    """Track message reactions"""

    def __init__(self, message_id: int, chat_id: int, initial_reaction: str):
        self.message_id = message_id
        self.chat_id = chat_id
        self.initial_reaction = initial_reaction
        self.current_reaction = initial_reaction
        self.state = "active"
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    async def cancel_all(self):
        for task in self.tasks:
            if not task.done():
                task.cancel()


class SimpleUserBot:
    def __init__(self):
        logger.info("📦 Initializing UserBot...")

        self.client = TelegramClient(
            f'sessions/{config.SESSION_NAME}',
            config.API_ID,
            config.API_HASH
        )
        self.last_action_time = 0
        self.my_user_id = None
        self.tracked_messages = {}

    async def check_rate_limit(self):
        """Flood control"""
        current_time = asyncio.get_event_loop().time()

        if current_time - self.last_action_time < MESSAGE_INTERVAL:
            wait_time = MESSAGE_INTERVAL - (current_time - self.last_action_time)
            await asyncio.sleep(wait_time)

        self.last_action_time = asyncio.get_event_loop().time()

    async def add_reaction(self, chat_id: int, message_id: int, reaction: str) -> bool:
        """Add reaction to message"""
        try:
            await self.check_rate_limit()
            reaction_obj = ReactionEmoji(emoticon=reaction)

            await self.client(SendReactionRequest(
                peer=chat_id,
                msg_id=message_id,
                reaction=[reaction_obj]
            ))

            logger.info(f"✅ Added {reaction} to msg {message_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding reaction: {e}")
            return False

    async def remove_reaction(self, chat_id: int, message_id: int) -> bool:
        """Remove reaction from message"""
        try:
            await self.check_rate_limit()

            await self.client(SendReactionRequest(
                peer=chat_id,
                msg_id=message_id,
                reaction=[]
            ))

            logger.info(f"🗑️  Removed reaction from msg {message_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error removing reaction: {e}")
            return False

    async def get_reactions(self, chat_id: int, message_id: int) -> dict:
        """Get reactions on message"""
        try:
            message = await self.client.get_messages(chat_id, ids=message_id)

            if not message or not message.reactions or not message.reactions.results:
                return {}

            return {r.reaction.emoticon: r.count for r in message.reactions.results}
        except Exception as e:
            logger.error(f"❌ Error getting reactions: {e}")
            return {}

    async def check_and_manage_reaction(
        self,
        message_id: int,
        chat_id: int,
        initial_reaction: str
    ):
        """Phase 1: Check after 20 sec and manage reaction"""
        try:
            tracker = self.tracked_messages.get(message_id)
            if not tracker:
                return

            await asyncio.sleep(CHECK_REMOVE_DELAY)
            reactions = await self.get_reactions(chat_id, message_id)

            if not reactions:
                # No reactions - remove ours
                await self.remove_reaction(chat_id, message_id)
                logger.info(f"📊 No reactions on {message_id}, removed ours")
                tracker.state = "removed"
                await self.monitor_for_new_reactions(message_id, chat_id, initial_reaction)
                return

            if len(reactions) == 1 and initial_reaction in reactions:
                # Only our reaction - remove and monitor
                await self.remove_reaction(chat_id, message_id)
                logger.info(f"📊 Only our reaction on {message_id}, removed")
                tracker.state = "removed"
                await self.monitor_for_new_reactions(message_id, chat_id, initial_reaction)
                return

            if initial_reaction in reactions and reactions[initial_reaction] > 1:
                # Others use our reaction - keep it
                logger.info(f"📊 Others copy our {initial_reaction} on {message_id}")
                tracker.state = "active"
                return

            # Check for popular reactions
            other_reactions = {k: v for k, v in reactions.items() if k != initial_reaction}
            if other_reactions:
                max_reaction = max(other_reactions.items(), key=lambda x: x[1])
                if max_reaction[1] >= SWITCH_THRESHOLD and initial_reaction in reactions:
                    logger.info(f"🔄 Switching from {initial_reaction} to {max_reaction[0]} on {message_id}")
                    await self.remove_reaction(chat_id, message_id)
                    await self.add_reaction(chat_id, message_id, max_reaction[0])
                    tracker.current_reaction = max_reaction[0]
                    tracker.state = "active"

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Error in check_and_manage_reaction: {e}")

    async def monitor_for_new_reactions(
        self,
        message_id: int,
        chat_id: int,
        initial_reaction: str,
        monitor_time: int = MONITOR_AFTER_REMOVE
    ):
        """Phase 2: Monitor for 5 minutes after removal"""
        try:
            tracker = self.tracked_messages.get(message_id)
            if not tracker:
                return

            logger.info(f"👀 Monitoring {message_id} for {monitor_time}s")

            start_time = datetime.utcnow()
            check_interval = 10

            while True:
                await asyncio.sleep(check_interval)

                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= monitor_time:
                    logger.info(f"⏱️  Monitoring finished for {message_id}")
                    tracker.state = "expired"
                    break

                reactions = await self.get_reactions(chat_id, message_id)

                if reactions and len(reactions) > 0:
                    logger.info(f"📊 New reactions on {message_id}: {reactions}")

                    if initial_reaction not in reactions:
                        logger.info(f"✨ Putting back {initial_reaction} on {message_id}")
                        await self.add_reaction(chat_id, message_id, initial_reaction)
                        tracker.current_reaction = initial_reaction
                        tracker.state = "active"

                    if len(reactions) > 1:
                        other_reactions = {k: v for k, v in reactions.items() if k != initial_reaction}
                        if other_reactions:
                            max_reaction = max(other_reactions.items(), key=lambda x: x[1])
                            if max_reaction[1] >= SWITCH_THRESHOLD:
                                logger.info(f"🔄 Switching to {max_reaction[0]} on {message_id}")
                                await self.remove_reaction(chat_id, message_id)
                                await self.add_reaction(chat_id, message_id, max_reaction[0])
                                tracker.current_reaction = max_reaction[0]

                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Error in monitor_for_new_reactions: {e}")
        finally:
            if message_id in self.tracked_messages:
                del self.tracked_messages[message_id]

    async def handle_new_message(self, event):
        """Handle new message"""
        try:
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

            # Random delay before reaction
            initial_delay = random.uniform(INITIAL_DELAY[0], INITIAL_DELAY[1])
            await asyncio.sleep(initial_delay)

            # Add reaction
            reaction = random.choice(REACTIONS)
            success = await self.add_reaction(event.chat_id, message.id, reaction)

            if success:
                tracker = MessageTracker(message.id, event.chat_id, reaction)
                self.tracked_messages[message.id] = tracker

                task = asyncio.create_task(
                    self.check_and_manage_reaction(
                        message.id,
                        event.chat_id,
                        reaction
                    )
                )
                tracker.add_task(task)

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
            logger.info(f"   😊 Reactions: {REACTIONS}")
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