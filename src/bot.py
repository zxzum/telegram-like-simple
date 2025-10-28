"""
Regular Telegram Bot - Controls the Userbot
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotController:
    """Controls userbot enable/disable state"""

    def __init__(self):
        self.userbot_enabled = False
        logger.info("🤖 Bot Controller initialized")

    def enable_userbot(self):
        """Enable userbot"""
        self.userbot_enabled = True
        logger.info("✅ Userbot ENABLED")

    def disable_userbot(self):
        """Disable userbot"""
        self.userbot_enabled = False
        logger.info("❌ Userbot DISABLED")

    def is_enabled(self):
        """Check if userbot is enabled"""
        return self.userbot_enabled


class RegularBot:
    """Regular Telegram Bot for controlling userbot"""

    def __init__(self, token: str, controller: BotController):
        self.token = token
        self.controller = controller
        self.application = None

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 Bot Control Panel\n\n"
            "/enable - Enable userbot\n"
            "/disable - Disable userbot\n"
            "/status - Check userbot status"
        )

    async def enable_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /enable command"""
        self.controller.enable_userbot()
        await update.message.reply_text("✅ Userbot has been ENABLED")
        logger.info(f"👤 User {update.effective_user.id} enabled userbot")

    async def disable_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /disable command"""
        self.controller.disable_userbot()
        await update.message.reply_text("❌ Userbot has been DISABLED")
        logger.info(f"👤 User {update.effective_user.id} disabled userbot")

    async def status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status = "✅ ENABLED" if self.controller.is_enabled() else "❌ DISABLED"
        await update.message.reply_text(f"Userbot Status: {status}")

    async def start(self):
        """Start the bot"""
        self.application = Application.builder().token(self.token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(CommandHandler("enable", self.enable_handler))
        self.application.add_handler(CommandHandler("disable", self.disable_handler))
        self.application.add_handler(CommandHandler("status", self.status_handler))

        logger.info("🤖 Regular Bot started")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()