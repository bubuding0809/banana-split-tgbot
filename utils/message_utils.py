"""
Message formatting and utility functions for the Banana Split Telegram bot.
"""

import logging
from typing import List, Literal, Optional
from telegram import helpers
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


class MessageUtils:
    """Utility class for message formatting and processing."""
    
    @staticmethod
    def escape_markdown(text: str, version: Literal[1, 2] = 2) -> str:
        """
        Escape markdown characters in text.
        
        Args:
            text: Text to escape
            version: Markdown version (1 or 2)
            
        Returns:
            Escaped text safe for markdown parsing
        """
        return helpers.escape_markdown(text, version=version)
    
    @staticmethod
    def mention_markdown(user_id: int, name: str, version: Literal[1, 2] = 2) -> str:
        """
        Create a markdown mention for a user.
        
        Args:
            user_id: Telegram user ID
            name: Display name for the mention
            version: Markdown version (1 or 2)
            
        Returns:
            Formatted markdown mention
        """
        return helpers.mention_markdown(user_id, name, version=version)
    
    @staticmethod
    def format_user_list(names: List[str], template: str = "> {name}") -> str:
        """
        Format a list of user names with a template.
        
        Args:
            names: List of user names
            template: Template string with {name} placeholder
            
        Returns:
            Formatted string with each name on a new line
        """
        if not names:
            return "> None"
        
        escaped_names = [MessageUtils.escape_markdown(name, version=2) for name in names]
        return "\n".join([template.format(name=name) for name in escaped_names])
    
    @staticmethod
    def format_member_management_result(
        success_list: List[str], 
        failed_list: List[str],
        message_template: str
    ) -> str:
        """
        Format the result of member management operations.
        
        Args:
            success_list: List of successfully processed members
            failed_list: List of failed member operations
            message_template: Template with {member_list} and {failed_list} placeholders
            
        Returns:
            Formatted result message
        """
        member_list = MessageUtils.format_user_list(success_list)
        failed_list_formatted = MessageUtils.format_user_list(failed_list)
        
        return message_template.format(
            member_list=member_list,
            failed_list=failed_list_formatted
        )
    
    @staticmethod
    def format_balance_message(user_list: List[str], deep_link_url: str) -> str:
        """
        Format a balance overview message.
        
        Args:
            user_list: List of user names
            deep_link_url: URL for the breakdown deep link
            
        Returns:
            Formatted balance message
        """
        balance_messages = []
        for user in user_list:
            user_mention = MessageUtils.mention_markdown(257256809, user, version=2)
            user_message = (
                f"🔵 *{user_mention}* • [🧾𝔹𝕣𝕖𝕒𝕜𝕕𝕠𝕨𝕟🧾]({deep_link_url})\n"
                f"> Owes Bubu $10\n"
                f"> Owes Shawnn $20\n"
            )
            balance_messages.append(user_message)
        
        text = "*Current Balances*:\n\n"
        text += "\n\n".join(balance_messages)
        return text
    
    @staticmethod
    def get_user_display_name(user) -> str:
        """
        Get a display name for a user, preferring first_name over user_id.
        
        Args:
            user: Telegram user object
            
        Returns:
            Display name string
        """
        return user.first_name or str(user.user_id)
    
    @staticmethod
    def format_group_instruction(bot_username: str, is_forum: bool = False) -> str:
        """
        Format instructions for using the bot in a group.
        
        Args:
            bot_username: The bot's username
            is_forum: Whether the group is a forum (supports topics)
            
        Returns:
            Formatted instruction message
        """
        if is_forum:
            return f"Use `/start@{MessageUtils.escape_markdown(bot_username)}` in your desired 💬 topic to start me\\!"
        else:
            return f"Use /start@{bot_username} to start me!"
    
    @staticmethod
    def format_template_message(template: str, **kwargs) -> str:
        """
        Format a message template with provided keyword arguments.
        
        Args:
            template: Message template with placeholders
            **kwargs: Values to substitute in the template
            
        Returns:
            Formatted message
        """
        return template.format(**kwargs)