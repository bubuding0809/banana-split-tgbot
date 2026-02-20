"""
Group command handlers for group chat interactions.
"""

import asyncio
import time
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import telegram

from .base_handler import BaseHandler
from messages import BotMessages
from utils import ChatUtils, KeyboardUtils, MessageUtils
from api import (
    CreateChatPayload,
    UpdateChatPayload,
    SendGroupReminderPayload,
    MigrateChatPayload,
)
from env import env


class GroupCommandHandler(BaseHandler):
    """Handler for group-specific commands."""

    async def start_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command in group chat.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        # Type assertions: validate_update ensures these are not None
        assert update.effective_chat is not None
        assert update.effective_user is not None

        message_thread_id = self.get_message_thread_id(update)

        # Handle thread ID update if in a topic
        if message_thread_id is not None:
            asyncio.create_task(
                self._update_chat_thread(update, context, message_thread_id)
            )

        # Create mini-app URL
        chat_context = ChatUtils.create_chat_context(
            update.effective_chat.id, update.effective_chat.type
        )

        url = ChatUtils.create_mini_app_url(
            env.MINI_APP_DEEPLINK, context.bot.username, chat_context, "compact"
        )

        keyboard = KeyboardUtils.create_mini_app_keyboard("🍌 Banana Splitz", url)

        pin_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=BotMessages.START_MESSAGE_GROUP,
            message_thread_id=message_thread_id,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboard,
        )

        # Try to pin the message
        try:
            await context.bot.pin_chat_message(
                chat_id=update.effective_chat.id, message_id=pin_message.id
            )
        except telegram.error.BadRequest:
            pass  # Ignore if pinning fails, likely due to permissions

    async def _update_chat_thread(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, thread_id: int
    ):
        """Update chat with thread ID for topic support."""
        # Type assertion: called after validation
        assert update.effective_chat is not None
        api = self.get_api_instance(context)
        if api is None:
            return

        payload = UpdateChatPayload(
            chat_id=update.effective_chat.id, thread_id=thread_id
        )
        api_result = await api.update_chat(payload)

        if isinstance(api_result, Exception):
            self.logger.error(f"api.update_chat error: {api_result}")
        else:
            self.logger.info(f"Chat updated: {api_result.chat}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=BotMessages.SUCCESS_TOPIC_DETECTED,
                message_thread_id=thread_id,
            )

    async def pin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /pin command to pin the mini-app message.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        # Type assertion: validate_update ensures this is not None
        assert update.effective_chat is not None

        message_thread_id = self.get_message_thread_id(update)

        if not self.check_mini_app_config():
            return await self.send_error_message(
                update, context, BotMessages.ERROR_MINI_APP_CONFIG, message_thread_id
            )

        # Create mini-app URL
        chat_context = ChatUtils.create_chat_context(
            update.effective_chat.id, update.effective_chat.type
        )

        url = ChatUtils.create_mini_app_url(
            env.MINI_APP_DEEPLINK, context.bot.username, chat_context, "compact"
        )

        keyboard = KeyboardUtils.create_mini_app_keyboard("🍌 Banana Splitz", url)

        pin_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=BotMessages.PIN_MESSAGE,
            reply_markup=keyboard,
            message_thread_id=message_thread_id,
        )

        try:
            await context.bot.pin_chat_message(
                chat_id=update.effective_chat.id,
                message_id=pin_message.id,
            )
        except telegram.error.BadRequest:
            await pin_message.reply_text(
                BotMessages.PIN_MANUAL_INSTRUCTION.format(
                    bot_username=context.bot.username
                )
            )

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /balance command to show current balances.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        # Type assertion: validate_update ensures this is not None
        assert update.effective_chat is not None

        message_thread_id = self.get_message_thread_id(update)

        if not self.check_mini_app_config():
            return await self.send_error_message(
                update, context, BotMessages.ERROR_MINI_APP_CONFIG, message_thread_id
            )

        # Create deep link URL for breakdown
        deep_link_url = ChatUtils.create_mini_app_url(
            env.MINI_APP_DEEPLINK, context.bot.username, "group", "compact"
        )

        # Mock user list (replace with actual API call)
        user_list = ["Jarrett", "Sean", "Bubu", "Shawnn"]

        balance_text = MessageUtils.format_balance_message(user_list, deep_link_url)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=balance_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
            message_thread_id=message_thread_id,
        )

    async def set_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /set_topic command to set the topic for notifications.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        # Type assertion: validate_update ensures this is not None
        assert update.effective_chat is not None

        message_thread_id = self.get_message_thread_id(update)

        # Validate that this is called in a topic
        if message_thread_id is None or not ChatUtils.is_forum_chat(
            update.effective_chat
        ):
            return await self.send_error_message(
                update, context, BotMessages.ERROR_TOPIC_ONLY, message_thread_id
            )

        api = self.get_api_instance(context)
        if api is None:
            return await self.send_error_message(
                update, context, BotMessages.ERROR_API_NOT_FOUND, message_thread_id
            )

        # Update chat with thread ID
        update_chat_payload = UpdateChatPayload(
            chat_id=update.effective_chat.id,
            thread_id=message_thread_id,
        )

        api_result = await api.update_chat(update_chat_payload)

        if isinstance(api_result, Exception):
            self.logger.error(f"api.update_chat error: {api_result}")
            return await self.send_error_message(
                update, context, BotMessages.ERROR_TOPIC_SET_FAILED, message_thread_id
            )

        self.logger.info(f"Topic set successfully: {api_result.chat}")
        await self.send_success_message(
            update, context, BotMessages.SUCCESS_TOPIC_SET, message_thread_id
        )

    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /summary command to show debt summary.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        # Type assertion: validate_update ensures this is not None
        assert update.effective_chat is not None

        # Only allow in group chats
        if self.is_private_chat(update):
            return await self.send_error_message(
                update, context, BotMessages.ERROR_SUMMARY_GROUP_ONLY, None
            )

        message_thread_id = self.get_message_thread_id(update)

        progress_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=BotMessages.SUMMARY_IN_PROGRESS,
            message_thread_id=message_thread_id,
        )

        api = self.get_api_instance(context)
        if api is None:
            return await self.send_error_message(
                update, context, BotMessages.ERROR_API_NOT_FOUND, message_thread_id
            )

        # Call the API to send group reminder
        payload = SendGroupReminderPayload(chat_id=update.effective_chat.id)
        api_result = await api.send_group_reminder(payload)

        # Delete the progress message
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=progress_message.id,
            )
        except telegram.error.BadRequest:
            pass

        if isinstance(api_result, Exception):
            self.logger.error(f"api.send_group_reminder error: {api_result}")
            return await self.send_error_message(
                update, context, BotMessages.ERROR_SUMMARY_FAILED, message_thread_id
            )

        # Handle different response scenarios
        if api_result.message_id is None:
            # No message was sent, show the reason
            reason_message = BotMessages.SUMMARY_NO_MESSAGE.format(
                reason=api_result.reason or "Unknown reason"
            )
            await self.send_success_message(
                update, context, reason_message, message_thread_id
            )

    async def bot_added(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle bot being added to a group via new_chat_members status update.

        This handles the case where the bot is added to an already existing group.
        For the case where the bot is included as an initial member during group
        creation, see handle_my_chat_member().

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        if update.message is None:
            return

        # Type assertion: validate_update ensures this is not None
        assert update.effective_chat is not None

        # Only handle group chats
        if self.is_private_chat(update):
            return

        new_members = update.message.new_chat_members
        if new_members is None:
            return

        # Check if the bot is in the new members
        bot = next(
            (
                member
                for member in new_members
                if member.username == context.bot.username
            ),
            None,
        )

        if bot is None:
            return

        # Deduplicate: when bot is added to an existing regular group, Telegram
        # sends both NEW_CHAT_MEMBERS and MY_CHAT_MEMBER updates. Only process
        # the first one to arrive.
        if not self._try_claim_chat_for_join(context, update.effective_chat.id):
            self.logger.info(
                f"Chat {update.effective_chat.id} already claimed by "
                "handle_my_chat_member, skipping bot_added"
            )
            return

        message_thread_id = self.get_message_thread_id(update)

        # Create chat in the API
        await self._create_chat_in_api(update, context, message_thread_id)

        # Send join message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=BotMessages.GROUP_JOIN_MESSAGE,
            message_thread_id=message_thread_id,
        )

        # Send usage instructions
        await self._send_usage_instructions(update, context, message_thread_id)

    async def handle_my_chat_member(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle my_chat_member updates for when the bot is added to a group.

        This handles the case where the bot is included as an initial member
        during group creation. Telegram sends a my_chat_member update instead
        of a new_chat_members message in this scenario.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if update.my_chat_member is None:
            return

        chat = update.my_chat_member.chat

        # Only handle regular group chats, not supergroups.
        # This handler targets the specific case where the bot is included as
        # an initial member during group creation (which is always a regular group).
        # Supergroups are excluded because:
        #   - Bot additions to existing supergroups are handled by bot_added()
        #     via new_chat_members
        #   - Group-to-supergroup migrations also trigger my_chat_member with
        #     LEFT->MEMBER in the new supergroup, which would incorrectly create
        #     a duplicate chat record alongside the migration handler
        if chat.type != telegram.constants.ChatType.GROUP:
            return

        old_status = update.my_chat_member.old_chat_member.status
        new_status = update.my_chat_member.new_chat_member.status

        # Check if bot was added (status changed from non-member to member)
        was_not_member = old_status in (
            telegram.constants.ChatMemberStatus.LEFT,
            telegram.constants.ChatMemberStatus.BANNED,
        )
        is_now_member = new_status in (
            telegram.constants.ChatMemberStatus.MEMBER,
            telegram.constants.ChatMemberStatus.ADMINISTRATOR,
            telegram.constants.ChatMemberStatus.RESTRICTED,
        )

        if not (was_not_member and is_now_member):
            return

        # Deduplicate: when bot is added to an existing regular group, Telegram
        # sends both NEW_CHAT_MEMBERS and MY_CHAT_MEMBER updates. Only process
        # the first one to arrive.
        if not self._try_claim_chat_for_join(context, chat.id):
            self.logger.info(
                f"Chat {chat.id} already claimed by bot_added, "
                "skipping handle_my_chat_member"
            )
            return

        self.logger.info(
            f"Bot added to group via my_chat_member: chat_id={chat.id}, "
            f"title={chat.title}, old_status={old_status}, new_status={new_status}"
        )

        # Create chat in the API (message_thread_id is not available for
        # my_chat_member updates)
        await self._create_chat_in_api(update, context, None)

        # Send join message
        await context.bot.send_message(
            chat_id=chat.id,
            text=BotMessages.GROUP_JOIN_MESSAGE,
        )

        # Send usage instructions
        await self._send_usage_instructions(update, context, None)

    def _try_claim_chat_for_join(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int
    ) -> bool:
        """
        Try to claim a chat for join processing to prevent duplicate messages.

        When a bot is added to an existing regular group, Telegram sends both
        a NEW_CHAT_MEMBERS message update and a MY_CHAT_MEMBER update. Both
        bot_added() and handle_my_chat_member() would fire, causing duplicate
        welcome messages. This method ensures only the first handler to process
        the event sends messages.

        This is safe without locks because there is no await between the
        dict check and set, so the asyncio event loop cannot interleave.

        Returns:
            True if this handler should proceed (first to claim), False otherwise.
        """
        processed = context.bot_data.setdefault("_processed_join_chats", {})
        now = time.monotonic()

        # Clean up entries older than 60 seconds to allow re-adding the bot
        expired = [k for k, v in processed.items() if now - v > 60]
        for k in expired:
            del processed[k]

        if chat_id in processed:
            return False

        processed[chat_id] = now
        return True

    async def _create_chat_in_api(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_thread_id: Optional[int],
    ):
        """Create the chat in the API when bot is added."""
        # Type assertions: called after validation
        assert update.effective_chat is not None
        api = self.get_api_instance(context)
        if api is None:
            return

        # Get chat photo if available
        full_chat = await context.bot.get_chat(chat_id=update.effective_chat.id)
        chat_photo_url = None

        if full_chat.photo is not None:
            photo = await context.bot.get_file(full_chat.photo.big_file_id)
            chat_photo_url = photo.file_path

        # Create chat payload
        payload = CreateChatPayload(
            chat_id=update.effective_chat.id,
            chat_title=update.effective_chat.title
            or f"Group:{update.effective_chat.id}",
            chat_type=update.effective_chat.type,
            chat_photo_url=chat_photo_url,
        )

        api_result = await api.create_chat(payload)

        if isinstance(api_result, Exception):
            self.logger.error(f"api.create_chat error: {api_result}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=BotMessages.ERROR_CHAT_INIT_FAILED,
                message_thread_id=message_thread_id,
            )
            return

        self.logger.info(f"Chat created: {api_result.message}")

    async def _send_usage_instructions(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_thread_id: Optional[int],
    ):
        """Send usage instructions after bot is added to group."""
        # Type assertion: called after validation
        assert update.effective_chat is not None
        instruction_text = MessageUtils.format_group_instruction(
            context.bot.username, ChatUtils.is_forum_chat(update.effective_chat)
        )

        parse_mode = (
            ParseMode.MARKDOWN_V2
            if ChatUtils.is_forum_chat(update.effective_chat)
            else None
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=instruction_text,
            message_thread_id=message_thread_id,
            parse_mode=parse_mode,
        )

    async def chat_id_migrated(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle chat ID migration when a group is upgraded to a supergroup.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        if update.message is None:
            return

        # Type assertion: validate_update ensures this is not None
        assert update.effective_chat is not None

        # Extract migration information from the message
        migrate_from_chat_id = update.message.migrate_from_chat_id
        migrate_to_chat_id = update.message.migrate_to_chat_id

        # Only process migration from the old group (when migrate_to_chat_id is present)
        # This prevents duplicate processing since Telegram sends two migration messages
        if migrate_to_chat_id is not None:
            # Current chat is being migrated to a supergroup - PROCESS THIS
            old_chat_id = update.effective_chat.id
            new_chat_id = migrate_to_chat_id
            self.logger.info(
                f"Processing migration from old group: {old_chat_id} -> {new_chat_id}"
            )
        elif migrate_from_chat_id is not None:
            # Current chat is the result of migration from a group - SKIP THIS
            self.logger.info(
                f"Received supergroup migration message (from {migrate_from_chat_id}), skipping to avoid duplicate processing"
            )
            return
        else:
            self.logger.warning("Migration update received but no migration IDs found")
            return

        api = self.get_api_instance(context)
        if api is None:
            self.logger.error("API instance not found, cannot handle chat migration")
            return

        # Call API to handle the migration
        payload = MigrateChatPayload(old_chat_id=old_chat_id, new_chat_id=new_chat_id)

        api_result = await api.migrate_chat(payload)

        if isinstance(api_result, Exception):
            self.logger.error(f"api.migrate_chat error: {api_result}")
        else:
            self.logger.info(
                f"Chat migration completed successfully: {api_result.message}"
            )

            # Send migration notification with new link
            await self._send_migration_notification(update, context, new_chat_id)

    async def _send_migration_notification(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, new_chat_id: int
    ):
        """
        Send migration notification message with new working link.

        Args:
            update: Telegram update object
            context: Bot context
            new_chat_id: The new chat ID after migration
        """
        # Type assertion: called after validation
        assert update.effective_chat is not None

        # Check mini-app configuration
        if not self.check_mini_app_config():
            self.logger.warning(
                "Mini-app config not available, skipping migration notification"
            )
            return

        try:
            message_thread_id = self.get_message_thread_id(update)

            # Create chat context using the NEW chat ID
            chat_context = ChatUtils.create_chat_context(
                new_chat_id, update.effective_chat.type
            )

            # Create mini-app URL with new chat context
            url = ChatUtils.create_mini_app_url(
                env.MINI_APP_DEEPLINK, context.bot.username, chat_context, "compact"
            )

            # Create keyboard with new link
            keyboard = KeyboardUtils.create_mini_app_keyboard("🍌 Banana Splitz", url)

            # Send migration notification message
            await context.bot.send_message(
                chat_id=new_chat_id,
                text=BotMessages.MIGRATION_MESSAGE_GROUP,
                message_thread_id=message_thread_id,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=keyboard,
            )

            self.logger.info(
                f"Migration notification sent successfully to chat {update.effective_chat.id}"
            )

        except Exception as e:
            self.logger.error(f"Failed to send migration notification: {e}")
            # Don't re-raise - we don't want messaging failure to break migration
