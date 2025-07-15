"""
Base handler class for Telegram bot command handlers.
"""

import logging
from typing import Optional, cast
from telegram import Update
from telegram.ext import ContextTypes
import telegram
from api import Api
from env import env

logger = logging.getLogger(__name__)


class BaseHandler:
    """Base class for all command handlers."""
    
    def __init__(self):
        """Initialize the base handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def send_typing_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Send typing action to indicate the bot is processing.
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        if update.effective_chat:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=telegram.constants.ChatAction.TYPING,
            )
    
    def get_api_instance(self, context: ContextTypes.DEFAULT_TYPE) -> Optional[Api]:
        """
        Get the API instance from bot context.
        
        Args:
            context: Bot context
            
        Returns:
            API instance or None if not found
        """
        api = context.bot_data.get("api")
        if api is None:
            self.logger.error("API instance not found in bot_data")
        return api
    
    def get_message_thread_id(self, update: Update) -> Optional[int]:
        """
        Extract message thread ID from update.
        
        Args:
            update: Telegram update object
            
        Returns:
            Message thread ID if available
        """
        return update.message.message_thread_id if update.message else None
    
    async def send_error_message(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        message: str,
        message_thread_id: Optional[int] = None
    ):
        """
        Send an error message to the user.
        
        Args:
            update: Telegram update object
            context: Bot context
            message: Error message to send
            message_thread_id: Optional thread ID for forum groups
        """
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                message_thread_id=message_thread_id,
            )
    
    async def send_success_message(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        message: str,
        message_thread_id: Optional[int] = None,
        parse_mode: Optional[str] = None
    ):
        """
        Send a success message to the user.
        
        Args:
            update: Telegram update object
            context: Bot context
            message: Success message to send
            message_thread_id: Optional thread ID for forum groups
            parse_mode: Optional parse mode for the message
        """
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                message_thread_id=message_thread_id,
                parse_mode=parse_mode,
            )
    
    def validate_update(self, update: Update) -> bool:
        """
        Validate that the update has required fields.
        
        Args:
            update: Telegram update object
            
        Returns:
            True if update is valid, False otherwise
        """
        return (
            update.effective_chat is not None and 
            update.effective_user is not None
        )
    
    def is_private_chat(self, update: Update) -> bool:
        """
        Check if the update is from a private chat.
        
        Args:
            update: Telegram update object
            
        Returns:
            True if private chat, False otherwise
        """
        return (
            update.effective_chat is not None and 
            update.effective_chat.type == telegram.constants.ChatType.PRIVATE
        )
    
    def is_group_chat(self, update: Update) -> bool:
        """
        Check if the update is from a group chat.
        
        Args:
            update: Telegram update object
            
        Returns:
            True if group chat, False otherwise
        """
        return (
            update.effective_chat is not None and 
            update.effective_chat.type in [
                telegram.constants.ChatType.GROUP,
                telegram.constants.ChatType.SUPERGROUP
            ]
        )
    
    def check_mini_app_config(self) -> bool:
        """
        Check if mini app configuration is available.
        
        Returns:
            True if mini app is configured, False otherwise
        """
        if env.MINI_APP_DEEPLINK is None:
            self.logger.error("MINI_APP_DEEPLINK was not set")
            return False
        return True