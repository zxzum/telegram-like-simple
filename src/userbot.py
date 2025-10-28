"""
Simple Telegram Userbot - Auto Reaction Logic with Smart Tracking
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
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
REACTIONS = ['👍', '❤️']  # Like and Heart
INITIAL_DELAY = (0.2, 1.0)  # Random delay before first reaction (sec)
CHECK_REMOVE_DELAY = 20  # Check if should remove after this time (sec)
MONITOR_AFTER_REMOVE = 300  # Monitor for 5 minutes after removal (sec)
MESSAGE_INTERVAL = 2  # Flood control between actions (sec)
SWITCH_THRESHOLD = 2  # Switch to other reaction if N+ people use it


class MessageTracker:
    """Track a single message's reactions"""

    def __init__(self, message_id: int, chat_id: int, initial_reaction: str):
        self.message_id = message_id
        self.chat_id = chat_id
        self.initial_reaction = initial_reaction
        self.current_reaction = initial_reaction
        self.created_at = datetime.utcnow()
        self.state = "active"  # active, removed, monitoring
        self.tasks = []

    def add_task(self, task):
        """Add task for cleanup"""
        self.tasks.append(task)

    async def cancel_all(self):
        """Cancel all pending tasks"""
        for task in self.tasks:
            if not task.done():
                task.cancel()

    def get_age(self) -> int:
        """Get message age in seconds"""
        return int((datetime.utcnow() - self.created_at).total_seconds())


class SimpleUserBot:
    def __init__(self):
        """Initialize the userbot"""
        logger.info("📦 Initializing SimpleUserBot...")

        self.client = TelegramClient(
            f'sessions/{config.SESSION_NAME}',
            config.API_ID,
            config.API_HASH
        )
        self.last_action_time = 0
        self.my_user_id = None
        # Track messages: {message_id: MessageTracker}
        self.tracked_messages = {}
        self.handler_registered = False

        logger.info(f"📦 TelegramClient created with session: sessions/{config.SESSION_NAME}")

    async def check_rate_limit(self):
        """Implement flood control"""
        current_time = asyncio.get_event_loop().time()

        if current_time - self.last_action_time < MESSAGE_INTERVAL:
            wait_time = MESSAGE_INTERVAL - (current_time - self.last_action_time)
            logger.debug(f"⏱️  Rate limiting: {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_action_time = asyncio.get_event_loop().time()

    async def add_reaction_to_message(self, chat_id: int, message_id: int, reaction: str) -> bool:
        """Add specific reaction to message"""
        try:
            await self.check_rate_limit()

            reaction_obj = ReactionEmoji(emoticon=reaction)

            logger.info(f"🔄 Adding reaction {reaction} to message {message_id}")

            await self.client(SendReactionRequest(
                peer=chat_id,
                msg_id=message_id,
                reaction=[reaction_obj]
            ))

            logger.info(f"✅ Added reaction {reaction} to message {message_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error adding reaction: {e}")
            return False

    async def remove_reaction_from_message(self, chat_id: int, message_id: int) -> bool:
        """Remove reaction from message"""
        try:
            await self.check_rate_limit()

            await self.client(SendReactionRequest(
                peer=chat_id,
                msg_id=message_id,
                reaction=[]
            ))

            logger.info(f"🗑️  Removed reaction from message {message_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error removing reaction: {e}")
            return False

    async def get_message_reactions(self, chat_id: int, message_id: int) -> dict:
        """Get reactions on message. Returns {emoji: count}"""
        try:
            message = await self.client.get_messages(chat_id, ids=message_id)

            if not message or not message.reactions or not message.reactions.results:
                return {}

            reactions_dict = {}
            for reaction in message.reactions.results:
                emoji = reaction.reaction.emoticon
                count = reaction.count
                reactions_dict[emoji] = count

            return reactions_dict

        except Exception as e:
            logger.error(f"❌ Error getting reactions: {e}")
            return {}

    async def check_and_manage_reaction(
        self,
        message_id: int,
        chat_id: int,
        initial_reaction: str
    ):
        """
        Phase 1: Check after 20 sec if only our reaction exists
        - If YES: remove it and enter monitoring phase
        - If NO: keep it
        """
        try:
            tracker = self.tracked_messages.get(message_id)
            if not tracker:
                return

            logger.debug(f"⏰ Phase 1: Checking message {message_id} after 20s...")
            await asyncio.sleep(CHECK_REMOVE_DELAY)

            reactions = await self.get_message_reactions(chat_id, message_id)
            logger.info(f"📊 Phase 1 check - Reactions: {reactions}")

            if not reactions:
                # No reactions at all
                await self.remove_reaction_from_message(chat_id, message_id)
                logger.info(f"🗑️  Phase 1: Removed {initial_reaction} (no reactions)")
                tracker.state = "removed"

                # Enter monitoring phase
                await self.monitor_for_new_reactions(message_id, chat_id, initial_reaction)
                return

            # Check if only our reaction exists
            if len(reactions) == 1 and initial_reaction in reactions:
                # Only our reaction
                await self.remove_reaction_from_message(chat_id, message_id)
                logger.info(f"🗑️  Phase 1: Removed {initial_reaction} (only ours)")
                tracker.state = "removed"

                # Enter monitoring phase
                await self.monitor_for_new_reactions(message_id, chat_id, initial_reaction)
                return

            # Check if anyone copied our reaction
            if initial_reaction in reactions and reactions[initial_reaction] > 1:
                logger.info(f"📊 Phase 1: Keeping {initial_reaction} (others use it too: {reactions[initial_reaction]} total)")
                tracker.state = "active"
                return

            # Other reactions exist, check if we should switch
            other_reactions = {k: v for k, v in reactions.items() if k != initial_reaction}
            if other_reactions:
                max_reaction = max(other_reactions.items(), key=lambda x: x[1])
                if max_reaction[1] >= SWITCH_THRESHOLD and initial_reaction in reactions:
                    # 2+ people use different reaction, switch to it
                    logger.info(f"🔄 Phase 1: Switching from {initial_reaction} to {max_reaction[0]} ({max_reaction[1]} people)")
                    await self.remove_reaction_from_message(chat_id, message_id)
                    await self.add_reaction_to_message(chat_id, message_id, max_reaction[0])
                    tracker.current_reaction = max_reaction[0]
                    tracker.state = "active"
                    return

        except asyncio.CancelledError:
            logger.debug(f"Phase 1 check cancelled for message {message_id}")
        except Exception as e:
            logger.error(f"❌ Error in check_and_manage_reaction: {e}")

    async def monitor_for_new_reactions(
        self,
        message_id: int,
        chat_id: int,
        initial_reaction: str,
        monitor_time: int = MONITOR_AFTER_REMOVE
    ):
        """
        Phase 2: Monitor for 5 minutes after removal
        - If someone reacts, put our reaction back
        - Only if our initial reaction attempt didn't work
        """
        try:
            tracker = self.tracked_messages.get(message_id)
            if not tracker:
                return

            logger.info(f"👀 Phase 2: Monitoring message {message_id} for {monitor_time}s...")

            start_time = datetime.utcnow()
            check_interval = 10  # Check every 10 seconds

            while True:
                await asyncio.sleep(check_interval)

                # Check if monitoring time exceeded
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= monitor_time:
                    logger.info(f"⏱️  Phase 2: Monitoring finished for message {message_id}")
                    tracker.state = "expired"
                    break

                reactions = await self.get_message_reactions(chat_id, message_id)

                if reactions and len(reactions) > 0:
                    logger.info(f"📊 Phase 2: New reactions appeared: {reactions}")

                    # Someone reacted! Put our reaction back
                    if initial_reaction not in reactions:
                        logger.info(f"✨ Phase 2: Putting back {initial_reaction}")
                        await self.add_reaction_to_message(chat_id, message_id, initial_reaction)
                        tracker.current_reaction = initial_reaction
                        tracker.state = "active"

                    # Check if should switch to more popular one
                    if len(reactions) > 1:
                        other_reactions = {k: v for k, v in reactions.items() if k != initial_reaction}
                        if other_reactions:
                            max_reaction = max(other_reactions.items(), key=lambda x: x[1])
                            if max_reaction[1] >= SWITCH_THRESHOLD:
                                logger.info(f"🔄 Phase 2: Switching to popular {max_reaction[0]}")
                                await self.remove_reaction_from_message(chat_id, message_id)
                                await self.add_reaction_to_message(chat_id, message_id, max_reaction[0])
                                tracker.current_reaction = max_reaction[0]

                    break

        except asyncio.CancelledError:
            logger.debug(f"Phase 2 monitoring cancelled for message {message_id}")
        except Exception as e:
            logger.error(f"❌ Error in monitor_for_new_reactions: {e}")
        finally:
            # Cleanup
            if message_id in self.tracked_messages:
                del self.tracked_messages[message_id]

    async def handle_new_message(self, event):
        """Handle new message event"""
        try:
            message = event.message

            logger.info(f"📨 New message {message.id}: {message.text[:50] if message.text else 'No text'}")

            # Ignore service messages
            if message.action:
                logger.debug(f"⏭️  Ignoring service message")
                return

            # Ignore own messages
            if config.IGNORE_OWN_MESSAGES and message.from_id:
                if isinstance(message.from_id, PeerUser):
                    if message.from_id.user_id == self.my_user_id:
                        logger.debug(f"⏭️  Ignoring own message")
                        return

            logger.info(f"✨ Processing message {message.id}")

            # Random initial delay before reaction (0.2-1 sec)
            initial_delay = random.uniform(INITIAL_DELAY[0], INITIAL_DELAY[1])
            logger.debug(f"⏱️  Initial delay: {initial_delay:.2f}s")
            await asyncio.sleep(initial_delay)

            # Choose and add random reaction
            reaction = random.choice(REACTIONS)
            success = await self.add_reaction_to_message(event.chat_id, message.id, reaction)

            if success:
                # Create tracker for this message
                tracker = MessageTracker(message.id, event.chat_id, reaction)
                self.tracked_messages[message.id] = tracker

                # Phase 1: Check after 20 sec
                task1 = asyncio.create_task(
                    self.check_and_manage_reaction(
                        message.id,
                        event.chat_id,
                        reaction
                    )
                )
                tracker.add_task(task1)

        except Exception as e:
            logger.error(f"❌ Error handling message: {e}", exc_info=True)

    async def start(self):
        """Start the userbot"""
        try:
            logger.info("🔐 Starting client connection...")
            await self.client.connect()
            logger.info("✅ Client connected")

            # Get current user ID
            me = await self.client.get_me()
            self.my_user_id = me.id

            logger.info("=" * 70)
            logger.info(f"🚀 USERBOT STARTED")
            logger.info(f"   👤 User: {me.username or me.first_name} (ID: {self.my_user_id})")
            logger.info(f"   💬 Chat ID: {config.CHAT_ID}")
            logger.info(f"   📌 Topic ID: {config.TOPIC_ID}")
            logger.info(f"   😊 Reactions: {REACTIONS}")
            logger.info(f"   ⏱️  Initial delay: {INITIAL_DELAY[0]}-{INITIAL_DELAY[1]}s")
            logger.info(f"   🔍 Check remove delay: {CHECK_REMOVE_DELAY}s")
            logger.info(f"   👀 Monitor after remove: {MONITOR_AFTER_REMOVE}s")
            logger.info(f"   🔄 Switch threshold: {SWITCH_THRESHOLD}+ people")
            logger.info(f"   🚫 Ignore own messages: {config.IGNORE_OWN_MESSAGES}")
            logger.info("=" * 70)

            logger.info("📝 Registering message handler...")

            # Register message handler
            @self.client.on(events.NewMessage(chats=config.CHAT_ID))
            async def message_handler(event):
                logger.debug(f"🔔 NEW MESSAGE EVENT TRIGGERED")

                message = event.message

                # Check topic filter
                if config.TOPIC_ID is not None and config.TOPIC_ID > 0:
                    has_reply_to = message.reply_to is not None

                    if not has_reply_to:
                        logger.debug(f"⏭️  Message not in topic (no reply_to)")
                        return

                    is_forum = getattr(message.reply_to, 'forum_topic', False)
                    if not is_forum:
                        logger.debug(f"⏭️  Message not in forum topic")
                        return

                    topic_msg_id = getattr(message.reply_to, 'reply_to_msg_id', None)
                    if topic_msg_id != config.TOPIC_ID:
                        logger.debug(f"⏭️  Message in different topic ({topic_msg_id} != {config.TOPIC_ID})")
                        return

                    logger.debug(f"✅ Message in correct topic")
                else:
                    logger.debug(f"✅ No topic filter, processing message")

                await self.handle_new_message(event)

            logger.info("✅ Message handler registered")
            self.handler_registered = True
            logger.info("👂 LISTENING FOR MESSAGES...\n")

            # Keep running
            await self.client.run_until_disconnected()

        except Exception as e:
            logger.error(f"❌ ERROR STARTING USERBOT: {e}", exc_info=True)
            raise