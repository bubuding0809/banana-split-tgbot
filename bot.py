import asyncio
import base64
import json
import logging
import os
from typing import Optional, cast
import telegram
from telegram import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    KeyboardButtonRequestUsers,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    helpers,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    Application,
)
from env import env
from api import (
    AddMemberPayload,
    Api,
    CreateChatPayload,
    CreateUserPayload,
    GetUserPayload,
    UpdateChatPayload,
)

# * Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

USAGE_GUIDE = """
1\\. **Add me to a group chat**: Click the "Add to group" button below or go to your group chat and add me as a member\\.

2\\. **Start the bot**: Use the `/start@{bot_username}` command in the group chat to kick things off\\. If your group has topics enabled, use the `/start@{bot_username}` command in your desired topic to receive notifications there\\.

3\\. **Get your friends to join**: Have them open the mini-app in the group chat\\. This will make them available for you to split expenses with\\.

🚀 Happy splitting\\! 🍌🍌🍌
"""

START_MESSAGE_EXISITING = """
Welcome back to Banana Splitz, {first_name}\\! 🌟 We're thrilled to see you again, here is how to use me.

{usage_guide}
"""

START_MESSAGE_PRIVATE = """
Welcome to Banana Splitz, {first_name}! 🎉

Say goodbye to awkward bill-splitting and hello to hassle-free group expenses! 

How to use me?
{usage_guide}
"""
START_MESSAGE_GROUP = """
🍌 Hey there homies 👋

Let me help you guys manage your shared expenses!

🤔 First time seeing me? 
⬇️ Get started with the app ⬇️
"""

HELP_MESSAGE = """
Forgot how to use the bot? 🤣

Here’s a quick guide to get you started:

{usage_guide}
"""

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

CHASE_USER_REQUEST, ADD_MEMBER_REQUEST = range(2)
ADD_MEMBER_COMMAND = "ADD_MEMBER"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat is None:
        return

    if update.effective_user is None:
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=telegram.constants.ChatAction.TYPING,
    )

    message_thread_id = update.message.message_thread_id if update.message else None

    api: Optional[Api] = context.bot_data.get("api")
    if api is None:
        return logger.error("[start]: Api instance not found in bot_data")

    # * Handle start process for private bot chat
    # * ==========================================
    if update.effective_chat.type == telegram.constants.ChatType.PRIVATE:
        # Show a loading message while fetching user data
        asyncio.create_task(
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⏳ Starting the bot...",
                message_thread_id=message_thread_id,
            )
        )

        # * Check if user exits
        get_user_result = await api.get_user(
            GetUserPayload(user_id=update.effective_user.id)
        )
        if isinstance(get_user_result, Exception):
            logger.error(f"[start] - api.get_user: {get_user_result}")
            return await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Something went wrong checking user, please try again.",
                message_thread_id=message_thread_id,
            )

        # * User exists - send welcome back message
        if get_user_result.user is not None:
            logger.info(f"[start] - api.get_user: User exists: {get_user_result.user}")
            return await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=START_MESSAGE_EXISITING.format(
                    first_name=helpers.escape_markdown(
                        update.effective_user.first_name
                    ),
                    usage_guide=USAGE_GUIDE.format(
                        bot_username=helpers.escape_markdown(context.bot.username)
                    ),
                ),
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(
                        text="Add to group",
                        url=helpers.create_deep_linked_url(
                            context.bot.username, "group_add", group=True
                        ),
                    )
                ),
                message_thread_id=message_thread_id,
                parse_mode=ParseMode.MARKDOWN_V2,
            )

        # * User does not exist - create user
        create_user_payload = CreateUserPayload(
            user_id=update.effective_user.id,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name,
            username=update.effective_user.username,
        )
        api_result = await api.create_user(create_user_payload)

        if isinstance(api_result, Exception):
            logger.error(f"[start] - api.create_user: {api_result}")
            return await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Something went wrong creating user, please try again.",
                message_thread_id=message_thread_id,
            )
        else:
            logger.info(
                f"[start] - api.create_user: User created: {api_result.message}"
            )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=START_MESSAGE_PRIVATE.format(
                first_name=helpers.escape_markdown(update.effective_user.first_name),
                usage_guide=USAGE_GUIDE.format(
                    bot_username=helpers.escape_markdown(context.bot.username)
                ),
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="Add to group",
                    url=helpers.create_deep_linked_url(
                        context.bot.username, "group_add", group=True
                    ),
                )
            ),
            message_thread_id=message_thread_id,
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    # * Handle start process for group chat
    # * ====================================
    else:

        async def update_chat_task(chat_id: int, thread_id: Optional[int] = None):
            payload = UpdateChatPayload(chat_id=chat_id, thread_id=thread_id)
            api_result = await api.update_chat(payload)
            if isinstance(api_result, Exception):
                logger.error(f"[start] - api.update_chat: {api_result}")
            else:
                logger.info(
                    f"[start] - api.update_chat: Chat updated: {api_result.chat}"
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="💬 Topic detected, I will now use this topic for all messages.",
                    message_thread_id=thread_id,
                )

        if message_thread_id is not None:
            asyncio.create_task(
                update_chat_task(
                    chat_id=update.effective_chat.id, thread_id=message_thread_id
                )
            )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=START_MESSAGE_GROUP,
            message_thread_id=message_thread_id,
        )

    # * Try to pin the bot for the chat
    # * ===============================

    if env.MINI_APP_DEEPLINK is None:
        logger.error("[pin]: MINI_APP_DEEPLINK was not set, unable to send pin message")

    chat_context = {
        "chat_id": update.effective_chat.id,
        "chat_type": update.effective_chat.type,
    }
    chat_context_bytes = json.dumps(chat_context).encode("utf-8")
    base64_encoded = base64.b64encode(chat_context_bytes).decode("utf-8")

    url = env.MINI_APP_DEEPLINK.format(
        botusername=context.bot.username, mode="compact", command=base64_encoded
    )
    inline_button = InlineKeyboardButton("Banana Splitz", url=url)
    reply_markup = InlineKeyboardMarkup.from_button(inline_button)

    pin_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Start splitting 🍌🍌🍌",
        reply_markup=reply_markup,
        message_thread_id=message_thread_id,
    )

    try:
        await context.bot.pin_chat_message(
            chat_id=update.effective_chat.id, message_id=pin_message.id
        )
    except telegram.error.BadRequest:
        await pin_message.reply_text(
            f"📌 Pin this for quick access, or make me admin and run /pin@{context.bot.username} again to pin automatically"
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    message_thread_id = update.message.message_thread_id if update.message else None

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=telegram.constants.ChatAction.TYPING,
        message_thread_id=message_thread_id,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Current operation cancelled.",
        message_thread_id=message_thread_id,
    )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    message_thread_id = update.message.message_thread_id if update.message else None

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=telegram.constants.ChatAction.TYPING,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=HELP_MESSAGE.format(
            usage_guide=USAGE_GUIDE.format(
                bot_username=helpers.escape_markdown(context.bot.username)
            ),
        ),
        message_thread_id=message_thread_id,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    message_thread_id = update.message.message_thread_id if update.message else None

    if env.MINI_APP_DEEPLINK is None:
        logger.error("[pin]: MINI_APP_DEEPLINK was not set, unable to send pin message")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Something went wrong, please try again.",
            message_thread_id=message_thread_id,
        )
        return

    chat_context = {
        "chat_id": update.effective_chat.id,
        "chat_type": update.effective_chat.type,
    }
    chat_context_bytes = json.dumps(chat_context).encode("utf-8")
    base64_encoded = base64.b64encode(chat_context_bytes).decode("utf-8")

    url = env.MINI_APP_DEEPLINK.format(
        botusername=context.bot.username, mode="compact", command=base64_encoded
    )
    inline_button = InlineKeyboardButton("Banana Splitz", url=url)
    reply_markup = InlineKeyboardMarkup.from_button(inline_button)

    pin_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🤑 Split your expense leh 🤑",
        reply_markup=reply_markup,
        message_thread_id=message_thread_id,
    )

    try:
        await context.bot.pin_chat_message(
            chat_id=update.effective_chat.id,
            message_id=pin_message.id,
        )
    except telegram.error.BadRequest:
        await pin_message.reply_text(
            f"📌 Pin this for quick access, or make me admin and run /pin@{context.bot.username} again to pin automatically"
        )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    message_thread_id = update.message.message_thread_id if update.message else None

    if env.MINI_APP_DEEPLINK is None:
        logger.error(
            "[balance]: MINI_APP_DEEPLINK was not set, unable to send balance message"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Something went wrong, please try again.",
            message_thread_id=message_thread_id,
        )
        return

    user_list = ["Jarrett", "Sean", "Bubu", "Shawnn"]
    balance_messages = []
    for user in user_list:
        deep_link_url = env.MINI_APP_DEEPLINK.format(
            botusername=context.bot.username, command="group", mode="compact"
        )
        user_mention = helpers.mention_markdown(257256809, user, version=2)
        user_message = (
            f"🔵 *{user_mention}* • [🧾𝔹𝕣𝕖𝕒𝕜𝕕𝕠𝕨𝕟🧾]({deep_link_url})\n"
            f"> Owes Bubu $10\n"
            f"> Owes Shawnn $20\n"
        )

        balance_messages.append(user_message)

    text = "*Current Balances*:\n\n"
    text += "\n\n".join(balance_messages)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
        message_thread_id=message_thread_id,
    )


async def chase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    if update.message is None:
        return

    if update.effective_chat.type != telegram.constants.ChatType.PRIVATE:
        await update.message.reply_text(
            text="⚠️ The 'chase' command is only available in your private chat with the bot"
        )
        return

    button = KeyboardButtonRequestUsers(
        request_id=0,
        user_is_bot=False,
        request_username=True,
    )

    reply_markup = ReplyKeyboardMarkup.from_button(
        KeyboardButton(
            text="Choose user",
            request_users=button,
        ),
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    if update.message:
        await update.message.reply_text(text="Select user", reply_markup=reply_markup)


async def user_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    if update.effective_sender is None:
        return

    users_shared = update.message.users_shared
    if users_shared is None:
        return

    if users_shared.request_id == ADD_MEMBER_REQUEST:
        user_data = context.user_data
        if user_data is None:
            return

        group_id = user_data.get("target_group_id")
        if group_id is None:
            logger.error("[user_shared] - ADD_MEMBER_REQUEST: group_id is None")
            return

        api = cast(Api, context.bot_data.get("api"))

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

        names = [user.first_name or str(user.user_id) for user in users_shared.users]

        success = []
        failure = []
        for api_result, name in zip(results, names):
            if isinstance(api_result, Exception):
                failure.append(name)
            else:
                success.append(name)

        logger.info(f"Added {', '.join(success)} to the group {group_id}")
        logger.info(f"Failed to add {', '.join(failure)} to the group {group_id}")

        text = ADD_MEMBER_END_MESSAGE.format(
            member_list=(
                "\n".join(
                    [
                        f"> {telegram.helpers.escape_markdown(name, version=2)}"
                        for name in success
                    ]
                )
                if success
                else "> None"
            ),
            failed_list=(
                "\n".join(
                    [
                        f"> {telegram.helpers.escape_markdown(name, version=2)}"
                        for name in failure
                    ]
                )
                if failure
                else "> None"
            ),
        )

        await update.message.reply_text(
            text=text,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    if users_shared.request_id == CHASE_USER_REQUEST:
        from_user = update.effective_sender
        shared_user = users_shared.users[0]

        try:
            await context.bot.send_message(
                shared_user.user_id,
                f"🤬💩REMINDER: FUCKING PAY BACK {from_user.username} LEH",
            )
        except telegram.error.Forbidden:
            await update.message.reply_text(
                text=f"⚠️ Failed to send message to {shared_user.username} as it was blocked.",
                reply_markup=ReplyKeyboardRemove(),
            )
        except telegram.error.BadRequest:
            await update.message.reply_text(
                text=f"⚠️ Failed to send message to {shared_user.username} as they do not have conversation yet.",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await update.message.reply_text(
                f"✅ Successfully reminded {shared_user.username} to pay up!",
                reply_markup=ReplyKeyboardRemove(),
            )


async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    if update.message is None:
        return

    if update.effective_chat.type == telegram.constants.ChatType.PRIVATE:
        return

    new_members = update.message.new_chat_members
    if new_members is None:
        return

    # Check if the bot is in the new members
    bot = next(
        filter(
            lambda x: x.username == context.bot.username,
            new_members,
        )
    )

    if bot is None:
        return

    message_thread_id = update.message.message_thread_id if update.message else None

    full_chat = await context.bot.get_chat(chat_id=update.effective_chat.id)

    chat_photo_url: Optional[str] = None
    if full_chat.photo is not None:
        photo = await context.bot.get_file(full_chat.photo.big_file_id)
        chat_photo_url = photo.file_path

    api: Optional[Api] = context.bot_data.get("api")
    if api is None:
        return logger.error("[bot_added]: Api instance not found in bot_data")

    payload = CreateChatPayload(
        chat_id=update.effective_chat.id,
        chat_title=update.effective_chat.title or f"Group:{update.effective_chat.id}",
        chat_type=update.effective_chat.type,
        chat_photo_url=chat_photo_url,
    )
    api_result = await api.create_chat(payload)

    if isinstance(api_result, Exception):
        logger.error(f"[bot_added] - api.create_chat: {api_result}")
        await update.message.reply_text(
            text="⚠️ Failed to properly initialize the chat. Please try again by removing and re-adding the bot.",
            message_thread_id=message_thread_id,
        )
        return

    logger.info(f"Chat created: {api_result.message}")
    await update.message.reply_text(
        text="🎉 Hello friends, I am here to help your split your expenses!",
        message_thread_id=message_thread_id,
    )

    if update.effective_chat.is_forum:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Use `/start@{helpers.escape_markdown(context.bot.username)}` in your desired 💬 topic to start using me\\!",
            message_thread_id=message_thread_id,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=helpers.escape_markdown(
                f"Use /start@{context.bot.username} to start using me!"
            ),
            message_thread_id=message_thread_id,
        )


async def set_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    if update.effective_user is None:
        return

    message_thread_id = update.message.message_thread_id if update.message else None

    if message_thread_id is None or not update.effective_chat.is_forum:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ This command can only be used in a topic.",
            message_thread_id=message_thread_id,
        )
        return

    api = cast(Optional[Api], context.bot_data.get("api"))
    if api is None:
        logger.error("[set_topic]: Api instance not found in bot_data")
        return

    update_chat_payload = UpdateChatPayload(
        chat_id=update.effective_chat.id,
        thread_id=message_thread_id,
    )
    api_result = await api.update_chat(update_chat_payload)
    if isinstance(api_result, Exception):
        logger.error(f"[set_topic] - api.update_chat: {api_result}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Failed to set topic. Please try again later.",
            message_thread_id=message_thread_id,
        )
        return

    logger.info(f"[set_topic] - api.update_chat: {api_result.chat}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✅ Topic set successfully! I will now use this topic for all messages.",
        message_thread_id=message_thread_id,
    )


async def add_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    if not context.args:
        logger.error("[add_member]: Empty add_member args")
        return

    group_id = context.args.pop()

    if not group_id.startswith(ADD_MEMBER_COMMAND):
        logger.error("[add_member]: Invalid parameter")
        return

    group_id = group_id.replace(ADD_MEMBER_COMMAND, "")

    # Make the group_id avaiable to the user_shared callback via context
    user_data = context.user_data
    if user_data is not None:
        user_data["target_group_id"] = group_id

    chat_info = await context.bot.get_chat(chat_id=group_id)
    cancel_button = KeyboardButton(
        text="/cancel",
    )
    button = KeyboardButton(
        text=f"Select Users 🧑‍🧒‍🧒",
        request_users=KeyboardButtonRequestUsers(
            request_id=1,
            request_name=True,
            request_username=True,
            max_quantity=telegram.constants.KeyboardButtonRequestUsersLimit.MAX_QUANTITY,
            user_is_bot=False,
        ),
    )

    text = ADD_MEMBER_START_MESSAGE.format(
        group_title=telegram.helpers.escape_markdown(chat_info.title or "", version=2)
    )
    await update.message.reply_text(
        text=text,
        reply_markup=ReplyKeyboardMarkup(
            [[cancel_button, button]], one_time_keyboard=True, resize_keyboard=True
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def error(update: Optional[object], context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a formatted message to the user/developer."""

    if context.error is None:
        return

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("[error]: Exception while handling an update:", exc_info=context.error)


async def post_init(application: Application):

    # * Set commands for the bot
    # *=============================================================================================

    # Commands for all chats
    common_commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Find out how to use the bot"),
    ]

    # Commands for private chats
    private_commands = [
        *common_commands,
        # BotCommand("chase", "Chase someone for payment"),
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
    # *=============================================================================================

    # * Set Api instance to the context
    application.bot_data["api"] = Api()


async def post_shutdown(application: Application):
    # * Clean up the API session
    api: Api = application.bot_data.get("api")
    if api is not None:
        await api.clean_up()


def main():
    application = (
        ApplicationBuilder()
        .token(env.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)
        .build()
    )

    # Define handlers
    start_handler = CommandHandler("start", start)
    cancel_handler = CommandHandler("cancel", cancel)
    help_handler = CommandHandler("help", help)
    pin_handler = CommandHandler("pin", pin)
    chase_handler = CommandHandler("chase", chase)
    set_topic_handler = CommandHandler("set_topic", set_topic)
    user_shared_handler = MessageHandler(
        filters.StatusUpdate.USERS_SHARED | filters.StatusUpdate.USER_SHARED,
        user_shared,
    )
    bot_added_handler = MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_added)
    balance_handler = CommandHandler("balance", balance)
    add_member_handler = CommandHandler(
        "start", add_member, filters.Regex(ADD_MEMBER_COMMAND)
    )

    # Register handlers
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

    # Special handler for general errors
    application.add_error_handler(error)

    # Run the bot in polling mode or webhook mode depending on the environment
    if env.ENV == "development":
        # * Run the bot in development mode with polling enabled
        logger.info("Running in development mode, using polling.")
        application.run_polling()
    else:
        # * Run the bot in production mode with webhook enabled
        logger.info(f"Running in {env.ENV} mode, using webhook.")
        logger.info(f"Webhook URL: {env.TELEGRAM_WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=env.PORT,
            secret_token=env.TELEGRAM_WEBHOOK_SECRET,
            webhook_url=env.TELEGRAM_WEBHOOK_URL,
        )


if __name__ == "__main__":
    main()
