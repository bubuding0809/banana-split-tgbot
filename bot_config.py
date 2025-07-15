"""
Bot configuration and setup for the Banana Split Telegram bot.
"""

import logging
from telegram import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from env import env
from api import Api
from handlers import UserCommandHandler, GroupCommandHandler, MemberManagementHandler
from messages import Constants

logger = logging.getLogger(__name__)


class BotConfiguration:
    """Configuration and setup class for the Telegram bot."""
    
    def __init__(self):
        """Initialize bot configuration."""
        self.user_handler = UserCommandHandler()
        self.group_handler = GroupCommandHandler()
        self.member_handler = MemberManagementHandler()
    
    def create_application(self) -> Application:
        """
        Create and configure the bot application.
        
        Returns:
            Configured Application instance
        """
        application = (
            ApplicationBuilder()
            .token(env.TELEGRAM_BOT_TOKEN)
            .post_init(self._post_init)
            .post_shutdown(self._post_shutdown)
            .concurrent_updates(True)
            .build()
        )
        
        self._register_handlers(application)
        return application
    
    def _register_handlers(self, application: Application):
        """
        Register all command and message handlers.
        
        Args:
            application: The bot application instance
        """
        # Create command handlers
        start_handler = CommandHandler("start", self._start_router)
        cancel_handler = CommandHandler("cancel", self.user_handler.cancel)
        help_handler = CommandHandler("help", self.user_handler.help)
        pin_handler = CommandHandler("pin", self.group_handler.pin)
        chase_handler = CommandHandler("chase", self.member_handler.chase)
        set_topic_handler = CommandHandler("set_topic", self.group_handler.set_topic)
        balance_handler = CommandHandler("balance", self.group_handler.balance)
        
        # Message handlers
        user_shared_handler = MessageHandler(
            filters.StatusUpdate.USERS_SHARED | filters.StatusUpdate.USER_SHARED,
            self.member_handler.user_shared,
        )
        bot_added_handler = MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS, 
            self.group_handler.bot_added
        )
        add_member_handler = CommandHandler(
            "start", 
            self.member_handler.add_member, 
            filters.Regex(Constants.ADD_MEMBER_COMMAND)
        )
        
        # Register handlers in correct order (most specific first)
        application.add_handler(help_handler)
        application.add_handler(pin_handler)
        application.add_handler(balance_handler)
        application.add_handler(chase_handler)
        application.add_handler(set_topic_handler)
        application.add_handler(user_shared_handler)
        application.add_handler(bot_added_handler)
        application.add_handler(add_member_handler)
        application.add_handler(cancel_handler)
        application.add_handler(start_handler)
        
        # Error handler
        application.add_error_handler(self._error_handler)
    
    async def _start_router(self, update, context):
        """
        Route /start command to appropriate handler based on chat type.
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        if not update.effective_chat:
            return
        
        if self.user_handler.is_private_chat(update):
            await self.user_handler.start_private(update, context)
        else:
            await self.group_handler.start_group(update, context)
    
    async def _post_init(self, application: Application):
        """
        Initialize bot after application setup.
        
        Args:
            application: The bot application instance
        """
        await self._setup_bot_commands(application)
        
        # Set API instance in bot_data
        application.bot_data["api"] = Api()
        
        logger.info("Bot initialization completed")
    
    async def _post_shutdown(self, application: Application):
        """
        Clean up resources during shutdown.
        
        Args:
            application: The bot application instance
        """
        # Clean up API session
        api = application.bot_data.get("api")
        if api is not None:
            await api.clean_up()
        
        logger.info("Bot shutdown completed")
    
    async def _setup_bot_commands(self, application: Application):
        """
        Set up bot commands for different chat scopes.
        
        Args:
            application: The bot application instance
        """
        # Common commands for all chats
        common_commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Find out how to use the bot"),
        ]
        
        # Commands for private chats
        private_commands = [
            *common_commands,
            # BotCommand("chase", "Chase someone for payment"),  # Commented out as in original
        ]
        await application.bot.set_my_commands(
            private_commands, scope=BotCommandScopeAllPrivateChats()
        )
        
        # Commands for group chats
        group_commands = [
            *common_commands,
            BotCommand("pin", "Pin the expenses mini-app"),
            BotCommand("balance", "View current split balances"),
            BotCommand("set_topic", "Set the topic for bot notifications"),
        ]
        await application.bot.set_my_commands(
            group_commands, scope=BotCommandScopeAllGroupChats()
        )
        
        logger.info("Bot commands configured successfully")
    
    async def _error_handler(self, update, context):
        """
        Handle errors that occur during update processing.
        
        Args:
            update: Telegram update object (may be None)
            context: Bot context
        """
        if context.error is None:
            return
        
        # Note: update may be None in some error cases, so we don't use it
        logger.error("Exception while handling an update:", exc_info=context.error)
    
    def run_bot(self):
        """
        Run the bot in either polling or webhook mode based on environment.
        """
        application = self.create_application()
        
        if env.ENV == "development":
            logger.info("Running in development mode, using polling.")
            application.run_polling()
        else:
            logger.info(f"Running in {env.ENV} mode, using webhook.")
            logger.info(f"Webhook URL: {env.TELEGRAM_WEBHOOK_URL}")
            application.run_webhook(
                listen="0.0.0.0",
                port=env.PORT,
                secret_token=env.TELEGRAM_WEBHOOK_SECRET,
                webhook_url=env.TELEGRAM_WEBHOOK_URL,
            )