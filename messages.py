"""
Message templates and constants for the Banana Split Telegram bot.
"""


class BotMessages:
    """Container for all bot message templates and constants."""

    # Usage and Help Messages
    USAGE_GUIDE = """
*Track Personal Expenses*: Send me a direct message\! For example:
```
15 USD Lunch
```
```
30000 JPY Japanese whiskey
``` \(Currency\)
```
200 beer, last friday
``` \(Date via comma\)
```
12 Grab ride yesterday
``` \(Simple Date\)

*Commands:*
\- `/list`: See your history
\- `/stats`: See your spending summary

*Group Expenses:*
1\. *Add me to a group chat*: Click the "Add to group" button below or go to your group chat and add me as a member\.
2\. *Start the bot*: Use the `/start@{bot_username}` command in the group chat to kick things off\.
3\. *Get your friends to join*: Have them open the mini\-app in the group chat to split expenses\.

🚀 Happy tracking and splitting\! 🍌🍌🍌
"""

    HELP_MESSAGE = """
Forgot how to use the bot? 🤣

Here's a quick guide to get you started:
{usage_guide}
"""

    # Start Messages - Private Chat
    START_MESSAGE_PRIVATE = """
Welcome to Banana Splitz, {first_name}\\! 🎉

Say goodbye to awkward bill\\-splitting and hello to hassle\\-free group expenses\\! 

How to use me?
{usage_guide}
"""

    START_MESSAGE_EXISTING = """
Welcome back to Banana Splitz, {first_name}\\! 🌟 We're thrilled to see you again, here is how to use me\\.
{usage_guide}
"""

    START_MESSAGE_GROUP_REGISTER = """
🎉 You are all set!

Learn more about me using /help

or

◀︎ Return to the app by swiping back
"""

    START_LOADER_MESSAGE = """⏳ Starting the bot..."""

    # Start Messages - Group Chat
    START_MESSAGE_GROUP = """
Let's split expenses together\\!

*👇 Everyone, open the app to get started*
"""

    GROUP_JOIN_MESSAGE = (
        """🎉 Hello friends, I am here to help your split your expenses!"""
    )

    MIGRATION_MESSAGE_GROUP = """
🔄 *Group Upgraded\\!*

This group has been upgraded to a supergroup\\. The old app button no longer works\\.

*👇 Use this button to access Banana Splitz*
"""

    # Member Management Messages
    ADD_MEMBER_START_MESSAGE = """
Your friends still haven\\'t joined the group? 🤔

> 🧑‍🧒‍🧒 {group_title} 🧑‍🧒‍🧒 


No worries, you can help them join by sharing their contact with me\\!

⌨️ Share via the keyboard button ⌨️
"""

    ADD_MEMBER_END_MESSAGE = """
🎉 Successfully added:
{member_list}


🚨 Failed to add:
{failed_list}
"""

    # Error and Status Messages
    ERROR_API_NOT_FOUND = (
        "⚠️ Something went wrong, API instance not found. Please try again."
    )
    ERROR_USER_CHECK_FAILED = "⚠️ Something went wrong checking user, please try again."
    ERROR_USER_CREATE_FAILED = "⚠️ Something went wrong creating user, please try again."
    ERROR_CHAT_INIT_FAILED = "⚠️ Failed to properly initialize the chat. Please try again by removing and re-adding the bot."
    ERROR_TOPIC_SET_FAILED = "⚠️ Failed to set topic. Please try again later."
    ERROR_MINI_APP_CONFIG = "Something went wrong, please try again."
    ERROR_CHASE_PRIVATE_ONLY = (
        "⚠️ The 'chase' command is only available in your private chat with the bot"
    )
    ERROR_TOPIC_ONLY = "⚠️ This command can only be used in a topic."
    ERROR_MESSAGE_SEND_BLOCKED = (
        "⚠️ Failed to send message to {username} as it was blocked."
    )
    ERROR_MESSAGE_SEND_NO_CONVERSATION = (
        "⚠️ Failed to send message to {username} as they do not have conversation yet."
    )
    ERROR_SUMMARY_GROUP_ONLY = (
        "⚠️ The 'summary' command can only be used in group chats."
    )
    ERROR_SUMMARY_FAILED = "⚠️ Failed to generate summary. Please try again later."

    # Success Messages
    SUCCESS_TOPIC_SET = (
        "✅ Topic set successfully! I will now use this topic for all messages."
    )
    SUCCESS_TOPIC_DETECTED = (
        "💬 Topic detected, I will now use this topic for all messages."
    )
    SUCCESS_CHASE_SENT = "✅ Successfully reminded {username} to pay up!"
    SUCCESS_OPERATION_CANCELLED = "Current operation cancelled."

    # Summary Messages
    SUMMARY_NO_MESSAGE = "💬 {reason}"
    SUMMARY_IN_PROGRESS = "⏳ Generating summary ..."

    # Pin and Balance Messages
    PIN_MESSAGE = "🤑 Split your expense leh 🤑"
    PIN_START_MESSAGE = "Start splitting 🍌🍌🍌"
    PIN_MANUAL_INSTRUCTION = "📌 Pin this for quick access, or make me admin and run /pin@{bot_username} again to pin automatically"

    BALANCE_HEADER = "*Current Balances*:"
    BALANCE_USER_TEMPLATE = "🔵 *{user_mention}* • [🧾𝔹𝕣𝕖𝕒𝕜𝕕𝕠𝕨𝕟🧾]({deep_link_url})\n> Owes Bubu $10\n> Owes Shawnn $20\n"

    # Chase Messages
    CHASE_REMINDER = "🤬💩REMINDER: FUCKING PAY BACK {from_username} LEH"
    CHASE_SELECT_USER = "Select user"
    CHASE_CHOOSE_USER_BUTTON = "Choose user"

    # Bot Instruction Messages for Groups
    GROUP_TOPIC_INSTRUCTION = (
        "Use `/start@{bot_username}` in your desired 💬 topic to start me\\!"
    )
    GROUP_START_INSTRUCTION = "Use `/start@{bot_username}` to start me\\!"

    # Personal Expense Messages
    EXPENSE_CREATED = "✅ Recorded: *{description}* — {currency} {amount}"
    EXPENSE_PARSE_HINT = (
        "💡 To log a personal expense, send a message like:\n"
        "  `12.50 Lunch`\n"
        "  `Grab ride 8.90`\n"
        "  `Coffee 5`\n"
        "  `25.50 Movie tickets, 2 days ago`"
    )
    ERROR_EXPENSE_CREATE_FAILED = (
        "⚠️ Failed to record expense. Please try again."
    )
    ERROR_EXPENSE_NOT_REGISTERED = (
        "⚠️ You need to /start the bot first before logging expenses."
    )
    EXPENSE_DELETED = "🗑 *Expense deleted\\.*"
    ERROR_EXPENSE_DELETE_FAILED = (
        "⚠️ Failed to delete expense. It may have already been removed."
    )

    # List & Stats Messages
    LIST_CHOOSE_PERIOD = "Choose a period"
    LIST_CANCELLED = "Cancelled\\."
    LIST_EMPTY = "No expenses recorded yet\\. Send a message like `12.50 Lunch` to get started\\!"
    LIST_NO_EXPENSES_FOR_PERIOD = "No expenses found for *{period_name}*\\."
    ERROR_LIST_FAILED = "⚠️ Failed to fetch expenses. Please try again."

    STATS_CHOOSE_PERIOD = "Choose a period"
    STATS_CANCELLED = "Cancelled\\."
    STATS_EMPTY = "No expenses recorded yet\\. Send a message like `12.50 Lunch` to get started\\!"
    STATS_NO_EXPENSES_FOR_PERIOD = "No expenses found for *{period_name}*\\."
    ERROR_STATS_FAILED = "⚠️ Failed to fetch expenses. Please try again."

    # Member Management UI
    ADD_MEMBER_SELECT_BUTTON = "Select Users 🧑‍🧒‍🧒"
    ADD_MEMBER_CANCEL_BUTTON = "/cancel"


class Constants:
    """Container for bot constants and configuration values."""

    # Request IDs for user sharing
    CHASE_USER_REQUEST = 0
    ADD_MEMBER_REQUEST = 1

    # Commands
    ADD_MEMBER_COMMAND = "ADD_MEMBER"

    # Response templates for member management
    MEMBER_LIST_SUCCESS_TEMPLATE = "> {name}"
    MEMBER_LIST_FAILED_TEMPLATE = "> {name}"
    MEMBER_LIST_NONE = "> None"
