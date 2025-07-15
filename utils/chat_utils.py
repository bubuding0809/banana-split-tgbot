"""
Chat-related utility functions for the Banana Split Telegram bot.
"""

import base64
import json
import logging
from typing import Dict, Any, Optional
from telegram import helpers

logger = logging.getLogger(__name__)


class ChatUtils:
    """Utility class for chat-related operations."""
    
    @staticmethod
    def create_chat_context(chat_id: int, chat_type: str) -> str:
        """
        Create a base64-encoded chat context for mini-app deep links.
        
        Args:
            chat_id: The Telegram chat ID
            chat_type: The type of chat (e.g., 'group', 'private')
            
        Returns:
            Base64-encoded string containing chat context
        """
        chat_context = {
            "chat_id": chat_id,
            "chat_type": chat_type,
        }
        chat_context_bytes = json.dumps(chat_context).encode("utf-8")
        return base64.b64encode(chat_context_bytes).decode("utf-8")
    
    @staticmethod
    def create_mini_app_url(
        deeplink_template: str, 
        bot_username: str, 
        command: str, 
        mode: str = "compact"
    ) -> str:
        """
        Create a mini-app URL using the provided template and parameters.
        
        Args:
            deeplink_template: The URL template with placeholders
            bot_username: The bot's username
            command: The command/context for the mini-app
            mode: The display mode for the mini-app
            
        Returns:
            Formatted mini-app URL
        """
        return deeplink_template.format(
            botusername=bot_username,
            mode=mode,
            command=command
        )
    
    @staticmethod
    def create_group_add_deep_link(bot_username: str) -> str:
        """
        Create a deep link for adding the bot to a group.
        
        Args:
            bot_username: The bot's username
            
        Returns:
            Deep link URL for group addition
        """
        return helpers.create_deep_linked_url(
            bot_username, "group_add", group=True
        )
    
    @staticmethod
    def get_message_thread_id(update) -> Optional[int]:
        """
        Extract message thread ID from an update.
        
        Args:
            update: Telegram update object
            
        Returns:
            Message thread ID if available, None otherwise
        """
        if update.message:
            return update.message.message_thread_id
        return None
    
    @staticmethod
    def is_forum_chat(chat) -> bool:
        """
        Check if a chat is a forum (supports topics).
        
        Args:
            chat: Telegram chat object
            
        Returns:
            True if the chat is a forum, False otherwise
        """
        return hasattr(chat, 'is_forum') and chat.is_forum