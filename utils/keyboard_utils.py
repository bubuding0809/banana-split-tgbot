"""
Keyboard-related utility functions for the Banana Split Telegram bot.
"""

import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.constants import KeyboardButtonRequestUsersLimit

logger = logging.getLogger(__name__)


class KeyboardUtils:
    """Utility class for creating keyboard markups."""
    
    @staticmethod
    def create_add_to_group_keyboard(url: str) -> InlineKeyboardMarkup:
        """
        Create an inline keyboard with 'Add to group' button.
        
        Args:
            url: The deep link URL for adding to group
            
        Returns:
            InlineKeyboardMarkup with the add to group button
        """
        return InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(text="Add to group", url=url)
        )
    
    @staticmethod
    def create_mini_app_keyboard(text: str, url: str) -> InlineKeyboardMarkup:
        """
        Create an inline keyboard with a mini-app button.
        
        Args:
            text: Button text
            url: Mini-app URL
            
        Returns:
            InlineKeyboardMarkup with the mini-app button
        """
        return InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(text, url=url)
        )
    
    @staticmethod
    def create_user_selection_keyboard(
        button_text: str, 
        request_id: int, 
        max_quantity: int = KeyboardButtonRequestUsersLimit.MAX_QUANTITY,
        request_name: bool = True,
        request_username: bool = True,
        user_is_bot: bool = False
    ) -> ReplyKeyboardMarkup:
        """
        Create a keyboard for user selection.
        
        Args:
            button_text: Text to display on the button
            request_id: Unique ID for this request
            max_quantity: Maximum number of users that can be selected
            request_name: Whether to request user names
            request_username: Whether to request usernames
            user_is_bot: Whether to allow bot selection
            
        Returns:
            ReplyKeyboardMarkup for user selection
        """
        button = KeyboardButton(
            text=button_text,
            request_users=KeyboardButtonRequestUsers(
                request_id=request_id,
                request_name=request_name,
                request_username=request_username,
                max_quantity=max_quantity,
                user_is_bot=user_is_bot,
            ),
        )
        return ReplyKeyboardMarkup.from_button(
            button, one_time_keyboard=True, resize_keyboard=True
        )
    
    @staticmethod
    def create_single_user_selection_keyboard(
        button_text: str, 
        request_id: int,
        request_username: bool = True,
        user_is_bot: bool = False
    ) -> ReplyKeyboardMarkup:
        """
        Create a keyboard for selecting a single user.
        
        Args:
            button_text: Text to display on the button
            request_id: Unique ID for this request
            request_username: Whether to request username
            user_is_bot: Whether to allow bot selection
            
        Returns:
            ReplyKeyboardMarkup for single user selection
        """
        button = KeyboardButtonRequestUsers(
            request_id=request_id,
            user_is_bot=user_is_bot,
            request_username=request_username,
        )
        
        reply_markup = ReplyKeyboardMarkup.from_button(
            KeyboardButton(text=button_text, request_users=button),
            one_time_keyboard=True,
            resize_keyboard=True,
        )
        return reply_markup
    
    @staticmethod
    def create_member_management_keyboard(
        select_button_text: str, 
        cancel_button_text: str,
        request_id: int
    ) -> ReplyKeyboardMarkup:
        """
        Create a keyboard for member management operations.
        
        Args:
            select_button_text: Text for the user selection button
            cancel_button_text: Text for the cancel button
            request_id: Unique ID for this request
            
        Returns:
            ReplyKeyboardMarkup with selection and cancel buttons
        """
        cancel_button = KeyboardButton(text=cancel_button_text)
        select_button = KeyboardButton(
            text=select_button_text,
            request_users=KeyboardButtonRequestUsers(
                request_id=request_id,
                request_name=True,
                request_username=True,
                max_quantity=KeyboardButtonRequestUsersLimit.MAX_QUANTITY,
                user_is_bot=False,
            ),
        )
        
        return ReplyKeyboardMarkup(
            [[cancel_button, select_button]], 
            one_time_keyboard=True, 
            resize_keyboard=True
        )
    
    @staticmethod
    def remove_keyboard() -> ReplyKeyboardRemove:
        """
        Create a keyboard removal markup.
        
        Returns:
            ReplyKeyboardRemove to hide the current keyboard
        """
        return ReplyKeyboardRemove()