"""
User command handlers for private chat interactions.
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .base_handler import BaseHandler
from messages import BotMessages
from utils import ChatUtils, KeyboardUtils, MessageUtils
from api import GetUserPayload, CreateUserPayload, CreateExpensePayload


@dataclass
class ParsedExpense:
    """Result of parsing a free-text expense message."""
    amount: float
    description: str
    currency: Optional[str] = None
    date: Optional[datetime] = None


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

    # Regex patterns used by parse_expense
    _AMOUNT_RE = re.compile(r"^\$?(\d+(?:\.\d{1,2})?)$")
    _CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
    _DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    @staticmethod
    def parse_expense(text: str) -> Optional[ParsedExpense]:
        """
        Parse an expense from free-text input.

        Tokenises the input and classifies each token as an amount,
        3-letter currency code, date ("yesterday" or YYYY-MM-DD), or
        description word.  Exactly one amount token is required; currency
        and date are optional (at most one each).  Everything left over
        becomes the description.

        Supported examples:
          - "12.50 Lunch"
          - "Lunch 12.50"
          - "$12.50 Lunch"
          - "30000 JPY Japanese whiskey"
          - "200 beer 2024-12-26"
          - "15 SGD Lunch yesterday"

        Args:
            text: Raw message text

        Returns:
            ParsedExpense or None if unparseable
        """
        text = text.strip()
        if not text:
            return None

        tokens = text.split()
        amount: Optional[float] = None
        currency: Optional[str] = None
        date: Optional[datetime] = None
        desc_parts: list[str] = []

        for token in tokens:
            # Try amount (only accept the first one found)
            if amount is None:
                # Strip leading $ for matching
                clean = token.lstrip("$")
                m = UserCommandHandler._AMOUNT_RE.match(clean)
                if m and token in (clean, f"${clean}"):
                    val = float(m.group(1))
                    if val > 0:
                        amount = val
                        continue

            # Try currency (uppercase 3-letter code, e.g. SGD, JPY)
            if currency is None and UserCommandHandler._CURRENCY_RE.match(token):
                currency = token
                continue

            # Try date — "yesterday" keyword
            if date is None and token.lower() == "yesterday":
                date = datetime.now(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=1)
                continue

            # Try date — YYYY-MM-DD
            if date is None and UserCommandHandler._DATE_RE.match(token):
                try:
                    date = datetime.strptime(token, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                    continue
                except ValueError:
                    pass  # invalid date like 2024-02-30, treat as description

            # Everything else is part of the description
            desc_parts.append(token)

        if amount is None:
            return None

        description = " ".join(desc_parts).strip()
        if not description:
            return None

        return ParsedExpense(
            amount=amount,
            description=description,
            currency=currency,
            date=date,
        )

    async def handle_personal_expense(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle a text message in a private DM as a personal expense.

        Parses the message for an amount and description, then calls the
        backend API to create a personal expense.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        assert update.effective_chat is not None
        assert update.effective_user is not None
        assert update.message is not None

        text = update.message.text
        if not text:
            return

        parsed = self.parse_expense(text)
        if parsed is None:
            # Could not parse — send a hint
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=BotMessages.EXPENSE_PARSE_HINT,
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        await self.send_typing_action(update, context)

        api = self.get_api_instance(context)
        if api is None:
            return await self.send_error_message(
                update, context, BotMessages.ERROR_API_NOT_FOUND
            )

        user_id = update.effective_user.id

        # Verify the user is registered before creating an expense
        get_user_result = await api.get_user(GetUserPayload(user_id=user_id))
        if isinstance(get_user_result, Exception):
            self.logger.error(f"api.get_user error: {get_user_result}")
            return await self.send_error_message(
                update, context, BotMessages.ERROR_EXPENSE_CREATE_FAILED
            )

        if get_user_result.user is None:
            return await self.send_error_message(
                update, context, BotMessages.ERROR_EXPENSE_NOT_REGISTERED
            )

        # Resolve the expense date (fall back to now)
        expense_date = parsed.date or datetime.now(timezone.utc)

        # Create the personal expense via REST API
        payload = CreateExpensePayload(
            chat_id=user_id,
            creator_id=user_id,
            payer_id=user_id,
            description=parsed.description,
            amount=parsed.amount,
            date=expense_date.isoformat(),
            split_mode="EQUAL",
            participant_ids=[user_id],
            send_notification=False,
            currency=parsed.currency,
        )

        result = await api.create_expense(payload)

        if isinstance(result, Exception):
            self.logger.error(f"api.create_expense error: {result}")
            return await self.send_error_message(
                update, context, BotMessages.ERROR_EXPENSE_CREATE_FAILED
            )

        if result.expense is None:
            self.logger.warning(
                f"api.create_expense returned no expense: {result.message}"
            )
            return await self.send_error_message(
                update, context, BotMessages.ERROR_EXPENSE_CREATE_FAILED
            )

        currency = result.expense.currency
        escaped_desc = MessageUtils.escape_markdown(parsed.description)
        escaped_currency = MessageUtils.escape_markdown(currency)
        formatted_amount = MessageUtils.escape_markdown(f"{parsed.amount:.2f}")

        confirmation = BotMessages.EXPENSE_CREATED.format(
            description=escaped_desc,
            currency=escaped_currency,
            amount=formatted_amount,
        )

        undo_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🗑 Undo",
                callback_data=f"undo_expense:{result.expense.id}",
            )]
        ])

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=confirmation,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=undo_keyboard,
        )

    async def handle_undo_expense(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle the inline 'Undo' button callback to delete a personal expense.

        Extracts the expense ID from callback_data, calls the backend
        DELETE endpoint, and edits the message to show deletion confirmation.

        Args:
            update: Telegram update object (callback query)
            context: Bot context
        """
        query = update.callback_query
        if query is None:
            return

        await query.answer()

        callback_data = query.data or ""
        if not callback_data.startswith("undo_expense:"):
            return

        expense_id = callback_data.split(":", 1)[1]

        api = self.get_api_instance(context)
        if api is None:
            await query.edit_message_text(
                text=BotMessages.ERROR_API_NOT_FOUND,
            )
            return

        result = await api.delete_expense(expense_id)

        if isinstance(result, Exception) or not result.success:
            self.logger.error(f"api.delete_expense error: {result}")
            await query.edit_message_text(
                text=BotMessages.ERROR_EXPENSE_DELETE_FAILED,
            )
            return

        await query.edit_message_text(
            text=BotMessages.EXPENSE_DELETED,
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    # Period definitions for /list callback data
    LIST_PERIODS: Dict[str, str] = {
        "list_period_today": "Today",
        "list_period_current_month": "Current month",
        "list_period_last_month": "Last month",
        "list_period_last_30_days": "Last 30 days",
        "list_period_last_12_months": "Last 12 months",
        "list_period_all_time": "All time",
        "list_period_cancel": "Cancel",
    }

    async def list_expenses(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle /list command — send an inline keyboard to choose a period.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        assert update.effective_chat is not None

        await self.send_typing_action(update, context)

        buttons = [
            [InlineKeyboardButton("Today", callback_data="list_period_today")],
            [InlineKeyboardButton("Current month", callback_data="list_period_current_month")],
            [InlineKeyboardButton("Last month", callback_data="list_period_last_month")],
            [InlineKeyboardButton("Last 30 days", callback_data="list_period_last_30_days")],
            [InlineKeyboardButton("Last 12 months", callback_data="list_period_last_12_months")],
            [InlineKeyboardButton("All time", callback_data="list_period_all_time")],
            [InlineKeyboardButton("Cancel", callback_data="list_period_cancel")],
        ]

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=BotMessages.LIST_CHOOSE_PERIOD,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    @staticmethod
    def _parse_expense_date(date_str: str) -> Optional[datetime]:
        """Parse an expense date string into a timezone-aware datetime."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            try:
                return datetime.strptime(date_str[:10], "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except (ValueError, AttributeError):
                return None

    async def handle_list_period(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle the inline period selection callback for /list.

        Fetches expenses, filters by the chosen period, groups by day,
        and formats a day-by-day expense listing.

        Args:
            update: Telegram update object (callback query)
            context: Bot context
        """
        query = update.callback_query
        if query is None:
            return

        await query.answer()

        callback_data = query.data or ""
        if not callback_data.startswith("list_period_"):
            return

        # Handle cancel
        if callback_data == "list_period_cancel":
            await query.edit_message_text(
                text=BotMessages.LIST_CANCELLED,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        period_name = self.LIST_PERIODS.get(callback_data, "Unknown")

        api = self.get_api_instance(context)
        if api is None:
            await query.edit_message_text(text=BotMessages.ERROR_API_NOT_FOUND)
            return

        assert update.effective_chat is not None
        chat_id = update.effective_chat.id

        result = await api.get_all_expenses(chat_id)

        if isinstance(result, Exception):
            self.logger.error(f"api.get_all_expenses error: {result}")
            await query.edit_message_text(text=BotMessages.ERROR_LIST_FAILED)
            return

        if not result.expenses:
            await query.edit_message_text(
                text=BotMessages.LIST_EMPTY,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        # Filter expenses by date range and attach parsed datetime
        start_dt, end_dt = self._get_period_range(callback_data)
        filtered: List[Tuple[datetime, object]] = []
        for exp in result.expenses:
            exp_dt = self._parse_expense_date(exp.date)
            if exp_dt is None:
                continue
            if start_dt and exp_dt < start_dt:
                continue
            if end_dt and exp_dt >= end_dt:
                continue
            filtered.append((exp_dt, exp))

        if not filtered:
            await query.edit_message_text(
                text=BotMessages.LIST_NO_EXPENSES_FOR_PERIOD.format(
                    period_name=MessageUtils.escape_markdown(period_name)
                ),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        # Sort by date descending
        filtered.sort(key=lambda x: x[0], reverse=True)

        # Group by calendar day
        from collections import OrderedDict
        days: OrderedDict[str, List] = OrderedDict()
        day_dates: Dict[str, datetime] = {}
        for exp_dt, exp in filtered:
            day_key = exp_dt.strftime("%Y-%m-%d")
            days.setdefault(day_key, []).append(exp)
            if day_key not in day_dates:
                day_dates[day_key] = exp_dt

        esc_period = MessageUtils.escape_markdown(period_name)

        # Build day sections
        day_sections: List[str] = []
        for day_key, exps in days.items():
            dt = day_dates[day_key]
            # Format: "1 March 2026, Sunday"
            day_label = f"{dt.day} {dt.strftime('%B')} {dt.year}, {dt.strftime('%A')}"

            # Compute per-currency daily totals for the header
            day_totals: Dict[str, float] = {}
            for exp in exps:
                day_totals[exp.currency] = day_totals.get(exp.currency, 0.0) + exp.amount

            total_parts = [f"-{amt:.10g} {cur}" for cur, amt in day_totals.items()]
            total_str = ", ".join(total_parts)

            esc_day_label = MessageUtils.escape_markdown(day_label)
            esc_total_str = MessageUtils.escape_markdown(f"({total_str})")

            # Build line items
            item_lines: List[str] = []
            for exp in exps:
                esc_amt = MessageUtils.escape_markdown(f"{exp.amount:.10g}")
                esc_cur = MessageUtils.escape_markdown(exp.currency)
                esc_desc = MessageUtils.escape_markdown(exp.description)
                item_lines.append(f"➖ {esc_amt} {esc_cur} — {esc_desc}")

            section = f"*{esc_day_label}* {esc_total_str}\n" + "\n".join(item_lines)
            day_sections.append(section)

        # Compute overall totals grouped by currency
        overall_totals: Dict[str, float] = {}
        for _exp_dt, exp in filtered:
            overall_totals[exp.currency] = overall_totals.get(exp.currency, 0.0) + exp.amount

        total_lines = [f"\\-{MessageUtils.escape_markdown(f'{amt:.10g}')} {MessageUtils.escape_markdown(cur)}"
                       for cur, amt in overall_totals.items()]

        lines = [
            f"*Expenses for {esc_period}*",
            "",
            "\n\n".join(day_sections),
            "",
            "*Total*",
            *total_lines,
        ]

        await query.edit_message_text(
            text="\n".join(lines),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    # Period definitions for /stats callback data
    STATS_PERIODS: Dict[str, str] = {
        "stats_period_today": "Today",
        "stats_period_current_month": "Current month",
        "stats_period_last_month": "Last month",
        "stats_period_last_30_days": "Last 30 days",
        "stats_period_last_12_months": "Last 12 months",
        "stats_period_all_time": "All time",
        "stats_period_cancel": "Cancel",
    }

    async def stats(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle /stats command — send an inline keyboard to choose a period.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not self.validate_update(update):
            return

        assert update.effective_chat is not None

        await self.send_typing_action(update, context)

        buttons = [
            [InlineKeyboardButton("Today", callback_data="stats_period_today")],
            [InlineKeyboardButton("Current month", callback_data="stats_period_current_month")],
            [InlineKeyboardButton("Last month", callback_data="stats_period_last_month")],
            [InlineKeyboardButton("Last 30 days", callback_data="stats_period_last_30_days")],
            [InlineKeyboardButton("Last 12 months", callback_data="stats_period_last_12_months")],
            [InlineKeyboardButton("All time", callback_data="stats_period_all_time")],
            [InlineKeyboardButton("Cancel", callback_data="stats_period_cancel")],
        ]

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=BotMessages.STATS_CHOOSE_PERIOD,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    @staticmethod
    def _get_period_range(period_key: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Return (start, end) datetimes for a given period key.

        Both bounds are inclusive-style: start <= date < end.
        Returns (None, None) for 'all_time'.

        Accepts keys with any prefix (e.g. 'stats_period_today',
        'list_period_today') — the prefix is stripped before matching.
        """
        # Strip known prefixes to get the bare period name
        for prefix in ("stats_period_", "list_period_"):
            if period_key.startswith(prefix):
                period_key = period_key[len(prefix):]
                break

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if period_key == "today":
            return today_start, today_start + timedelta(days=1)

        if period_key == "current_month":
            month_start = today_start.replace(day=1)
            return month_start, None  # up to now

        if period_key == "last_month":
            this_month_start = today_start.replace(day=1)
            last_month_end = this_month_start
            if this_month_start.month == 1:
                last_month_start = this_month_start.replace(
                    year=this_month_start.year - 1, month=12
                )
            else:
                last_month_start = this_month_start.replace(
                    month=this_month_start.month - 1
                )
            return last_month_start, last_month_end

        if period_key == "last_30_days":
            return today_start - timedelta(days=30), None

        if period_key == "last_12_months":
            twelve_months_ago = today_start.replace(
                year=today_start.year - 1
            )
            return twelve_months_ago, None

        # all_time
        return None, None

    async def handle_stats_period(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle the inline period selection callback for /stats.

        Filters expenses by the chosen period, groups by description
        (capitalized), and formats a detailed statistics message.

        Args:
            update: Telegram update object (callback query)
            context: Bot context
        """
        query = update.callback_query
        if query is None:
            return

        await query.answer()

        callback_data = query.data or ""
        if not callback_data.startswith("stats_period_"):
            return

        # Handle cancel
        if callback_data == "stats_period_cancel":
            await query.edit_message_text(
                text=BotMessages.STATS_CANCELLED,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        period_name = self.STATS_PERIODS.get(callback_data, "Unknown")

        api = self.get_api_instance(context)
        if api is None:
            await query.edit_message_text(text=BotMessages.ERROR_API_NOT_FOUND)
            return

        assert update.effective_chat is not None
        chat_id = update.effective_chat.id

        result = await api.get_all_expenses(chat_id)

        if isinstance(result, Exception):
            self.logger.error(f"api.get_all_expenses error: {result}")
            await query.edit_message_text(text=BotMessages.ERROR_STATS_FAILED)
            return

        if not result.expenses:
            await query.edit_message_text(
                text=BotMessages.STATS_EMPTY,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        # Filter expenses by date range
        start_dt, end_dt = self._get_period_range(callback_data)
        filtered: List = []
        for exp in result.expenses:
            exp_dt = self._parse_expense_date(exp.date)
            if exp_dt is None:
                continue

            if start_dt and exp_dt < start_dt:
                continue
            if end_dt and exp_dt >= end_dt:
                continue
            filtered.append(exp)

        if not filtered:
            await query.edit_message_text(
                text=BotMessages.STATS_NO_EXPENSES_FOR_PERIOD.format(
                    period_name=MessageUtils.escape_markdown(period_name)
                ),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        # Group filtered expenses by currency
        by_currency: Dict[str, List] = {}
        for exp in filtered:
            by_currency.setdefault(exp.currency, []).append(exp)

        esc_period = MessageUtils.escape_markdown(period_name)

        # Build a section per currency
        currency_sections: List[str] = []

        for currency, exps in by_currency.items():
            esc_currency = MessageUtils.escape_markdown(currency)
            cur_total = sum(exp.amount for exp in exps)
            esc_cur_total = MessageUtils.escape_markdown(f"{cur_total:.2f}")

            currency_sections.append(
                f"*{esc_currency}*\nTotal: {esc_cur_total} {esc_currency}"
            )

        # Build the final message
        lines = [
            f"*Statistics for {esc_period}*",
            "",
            "*➖ Expenses*",
            "",
            "\n\n".join(currency_sections),
        ]

        await query.edit_message_text(
            text="\n".join(lines),
            parse_mode=ParseMode.MARKDOWN_V2,
        )