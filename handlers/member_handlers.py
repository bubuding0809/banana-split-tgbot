"""
Member management handlers for adding/managing group members and chasing users.
"""

import asyncio
from typing import cast
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import telegram

from .base_handler import BaseHandler
from messages import BotMessages, Constants
from utils import KeyboardUtils, MessageUtils
from api import Api, AddMemberPayload


class MemberManagementHandler(BaseHandler):
    """Handler for member management operations."""
    
    async def add_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command with ADD_MEMBER parameter for adding members to groups.
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        if update.message is None:
            return
        
        if not context.args:
            self.logger.error("Empty add_member args")
            return
        
        group_id = context.args.pop()
        
        if not group_id.startswith(Constants.ADD_MEMBER_COMMAND):
            self.logger.error("Invalid parameter")
            return
        
        group_id = group_id.replace(Constants.ADD_MEMBER_COMMAND, "")
        
        # Store group_id in user_data for the user_shared callback
        user_data = context.user_data
        if user_data is not None:
            user_data["target_group_id"] = group_id
        
        # Get chat information
        chat_info = await context.bot.get_chat(chat_id=group_id)
        
        # Create keyboard for member selection
        keyboard = KeyboardUtils.create_member_management_keyboard(
            BotMessages.ADD_MEMBER_SELECT_BUTTON,
            BotMessages.ADD_MEMBER_CANCEL_BUTTON,
            Constants.ADD_MEMBER_REQUEST
        )
        
        message_text = BotMessages.ADD_MEMBER_START_MESSAGE.format(
            group_title=MessageUtils.escape_markdown(chat_info.title or "", version=2)
        )
        
        await update.message.reply_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    
    async def chase(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /chase command for chasing users for payment.
        
        Args:
            update: Telegram update object
            context: Bot context (required for handler signature)
        """
        if update.message is None:
            return
        
        # Only allow in private chats
        if not self.is_private_chat(update):
            await update.message.reply_text(
                text=BotMessages.ERROR_CHASE_PRIVATE_ONLY
            )
            return
        
        # Create user selection keyboard
        keyboard = KeyboardUtils.create_single_user_selection_keyboard(
            BotMessages.CHASE_CHOOSE_USER_BUTTON,
            Constants.CHASE_USER_REQUEST,
            request_username=True,
            user_is_bot=False
        )
        
        await update.message.reply_text(
            text=BotMessages.CHASE_SELECT_USER, 
            reply_markup=keyboard
        )
    
    async def user_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle user sharing events for both member addition and chasing.
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        if update.message is None or update.effective_sender is None:
            return
        
        users_shared = update.message.users_shared
        if users_shared is None:
            return
        
        if users_shared.request_id == Constants.ADD_MEMBER_REQUEST:
            await self._handle_add_member_shared(update, context, users_shared)
        elif users_shared.request_id == Constants.CHASE_USER_REQUEST:
            await self._handle_chase_user_shared(update, context, users_shared)
    
    async def _handle_add_member_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE, users_shared):
        """Handle users shared for adding members to a group."""
        # Type assertion: called from user_shared which checks for None
        assert update.message is not None
        user_data = context.user_data
        if user_data is None:
            return
        
        group_id = user_data.get("target_group_id")
        if group_id is None:
            self.logger.error("group_id is None in ADD_MEMBER_REQUEST")
            return
        
        api = cast(Api, self.get_api_instance(context))
        if api is None:
            return
        
        # Create add member tasks for all shared users
        add_member_tasks = [
            api.add_member(
                AddMemberPayload(
                    chat_id=int(group_id),
                    user_id=user.user_id,
                    first_name=user.first_name or "",
                    last_name=user.last_name,
                    username=user.username,
                )
            )
            for user in users_shared.users
        ]
        
        results = await asyncio.gather(*add_member_tasks)
        
        # Process results
        names = [MessageUtils.get_user_display_name(user) for user in users_shared.users]
        success_list = []
        failed_list = []
        
        for api_result, name in zip(results, names):
            if isinstance(api_result, Exception):
                failed_list.append(name)
            else:
                success_list.append(name)
        
        self.logger.info(f"Added {', '.join(success_list)} to group {group_id}")
        self.logger.info(f"Failed to add {', '.join(failed_list)} to group {group_id}")
        
        # Format and send result message
        result_text = MessageUtils.format_member_management_result(
            success_list, 
            failed_list,
            BotMessages.ADD_MEMBER_END_MESSAGE
        )
        
        await update.message.reply_text(
            text=result_text,
            reply_markup=KeyboardUtils.remove_keyboard(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    
    async def _handle_chase_user_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE, users_shared):
        """Handle user shared for chasing payment."""
        # Type assertions: called from user_shared which checks for None
        assert update.message is not None
        assert update.effective_sender is not None
        
        from_user = update.effective_sender
        shared_user = users_shared.users[0]
        
        chase_message = BotMessages.CHASE_REMINDER.format(
            from_username=from_user.username
        )
        
        try:
            await context.bot.send_message(shared_user.user_id, chase_message)
            
            success_message = BotMessages.SUCCESS_CHASE_SENT.format(
                username=shared_user.username
            )
            await update.message.reply_text(
                text=success_message,
                reply_markup=KeyboardUtils.remove_keyboard(),
            )
            
        except telegram.error.Forbidden:
            error_message = BotMessages.ERROR_MESSAGE_SEND_BLOCKED.format(
                username=shared_user.username
            )
            await update.message.reply_text(
                text=error_message,
                reply_markup=KeyboardUtils.remove_keyboard(),
            )
            
        except telegram.error.BadRequest:
            error_message = BotMessages.ERROR_MESSAGE_SEND_NO_CONVERSATION.format(
                username=shared_user.username
            )
            await update.message.reply_text(
                text=error_message,
                reply_markup=KeyboardUtils.remove_keyboard(),
            )