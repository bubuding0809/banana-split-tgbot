"""
User command handlers for private chat interactions.
"""

import asyncio
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .base_handler import BaseHandler
from messages import BotMessages
from utils import ChatUtils, KeyboardUtils, MessageUtils
from api import GetUserPayload, CreateUserPayload


class UserCommandHandler(BaseHandler):
    """Handler for user-specific commands in private chats."""
    
    async def start_private(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command in private chat.
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return
        
        # Type assertions: validate_update ensures these are not None
        assert update.effective_chat is not None
        assert update.effective_user is not None
        
        await self.send_typing_action(update, context)
        
        message_thread_id = self.get_message_thread_id(update)
        start_command_arg = context.args[0] if context.args else None
        
        api = self.get_api_instance(context)
        if api is None:
            return await self.send_error_message(
                update, context, BotMessages.ERROR_API_NOT_FOUND, message_thread_id
            )
        
        # Show loading message
        asyncio.create_task(
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=BotMessages.START_LOADER_MESSAGE,
                message_thread_id=message_thread_id,
            )
        )
        
        # Check if user exists
        get_user_result = await api.get_user(
            GetUserPayload(user_id=update.effective_user.id)
        )
        
        if isinstance(get_user_result, Exception):
            self.logger.error(f"api.get_user error: {get_user_result}")
            return await self.send_error_message(
                update, context, BotMessages.ERROR_USER_CHECK_FAILED, message_thread_id
            )
        
        # Handle existing user
        if get_user_result.user is not None:
            self.logger.info(f"User exists: {get_user_result.user}")
            
            if start_command_arg == "register":
                return await self.send_success_message(
                    update, context, BotMessages.START_MESSAGE_GROUP_REGISTER
                )
            
            return await self._send_existing_user_message(update, context, message_thread_id)
        
        # Create new user
        await self._create_new_user(update, context, message_thread_id, start_command_arg)
    
    async def _send_existing_user_message(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        message_thread_id: Optional[int]
    ):
        """Send welcome back message for existing users."""
        # Type assertions: called after validate_update
        assert update.effective_chat is not None
        assert update.effective_user is not None
        usage_guide = BotMessages.USAGE_GUIDE.format(
            bot_username=MessageUtils.escape_markdown(context.bot.username)
        )
        
        message_text = BotMessages.START_MESSAGE_EXISTING.format(
            first_name=MessageUtils.escape_markdown(update.effective_user.first_name),
            usage_guide=usage_guide
        )
        
        deep_link_url = ChatUtils.create_group_add_deep_link(context.bot.username)
        keyboard = KeyboardUtils.create_add_to_group_keyboard(deep_link_url)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            reply_markup=keyboard,
            message_thread_id=message_thread_id,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    
    async def _create_new_user(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        message_thread_id: Optional[int],
        start_command_arg: Optional[str]
    ):
        """Create a new user and send welcome message."""
        # Type assertions: called after validate_update
        assert update.effective_chat is not None
        assert update.effective_user is not None
        api = self.get_api_instance(context)
        if api is None:
            return
        
        create_user_payload = CreateUserPayload(
            user_id=update.effective_user.id,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name,
            username=update.effective_user.username,
        )
        
        api_result = await api.create_user(create_user_payload)
        
        if isinstance(api_result, Exception):
            self.logger.error(f"api.create_user error: {api_result}")
            return await self.send_error_message(
                update, context, BotMessages.ERROR_USER_CREATE_FAILED, message_thread_id
            )
        
        self.logger.info(f"User created: {api_result.message}")
        
        if start_command_arg == "register":
            return await self.send_success_message(
                update, context, BotMessages.START_MESSAGE_GROUP_REGISTER
            )
        
        await self._send_new_user_welcome(update, context, message_thread_id)
    
    async def _send_new_user_welcome(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        message_thread_id: Optional[int]
    ):
        """Send welcome message for new users."""
        # Type assertions: called after validate_update
        assert update.effective_chat is not None
        assert update.effective_user is not None
        usage_guide = BotMessages.USAGE_GUIDE.format(
            bot_username=MessageUtils.escape_markdown(context.bot.username)
        )
        
        message_text = BotMessages.START_MESSAGE_PRIVATE.format(
            first_name=MessageUtils.escape_markdown(update.effective_user.first_name),
            usage_guide=usage_guide
        )
        
        deep_link_url = ChatUtils.create_group_add_deep_link(context.bot.username)
        keyboard = KeyboardUtils.create_add_to_group_keyboard(deep_link_url)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            reply_markup=keyboard,
            message_thread_id=message_thread_id,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /help command.
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return
        
        # Type assertion: validate_update ensures this is not None
        assert update.effective_chat is not None
        
        await self.send_typing_action(update, context)
        
        message_thread_id = self.get_message_thread_id(update)
        
        usage_guide = BotMessages.USAGE_GUIDE.format(
            bot_username=MessageUtils.escape_markdown(context.bot.username)
        )
        
        message_text = BotMessages.HELP_MESSAGE.format(usage_guide=usage_guide)
        
        await self.send_success_message(
            update, 
            context, 
            message_text,
            message_thread_id,
            ParseMode.MARKDOWN_V2
        )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /cancel command.
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return
        
        # Type assertion: validate_update ensures this is not None
        assert update.effective_chat is not None
        
        message_thread_id = self.get_message_thread_id(update)
        
        await self.send_typing_action(update, context)
        await self.send_success_message(
            update, context, BotMessages.SUCCESS_OPERATION_CANCELLED, message_thread_id
        )