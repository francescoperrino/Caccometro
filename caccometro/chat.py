"""Helpers on Telegram updates shared by the commands and the message handler."""
import logging

from telegram import Update
from telegram.constants import ChatMemberStatus, MessageLimit
from telegram.ext import ContextTypes

from caccometro.database import User, upsert_user

logger = logging.getLogger(__name__)


def display_name_of(tg_user):
    """Name shown for users without a username: their full name, falling back to the numeric ID."""
    return tg_user.full_name or str(tg_user.id)


def register_user(chat_id, tg_user):
    """Store the current username/name of a Telegram user and return it as a database.User."""
    user = User(tg_user.id, tg_user.username, display_name_of(tg_user))
    upsert_user(chat_id, user.user_id, user.username, user.display_name)
    return user


def register_sender(update: Update):
    """Record the sender of the message in the users table and return it.

    Returns None when there is no usable sender (channel posts, anonymous admins, bots).
    """
    tg_user = update.message.from_user if update.message else None
    if tg_user is None or tg_user.is_bot:
        return None
    return register_user(update.message.chat_id, tg_user)


def where(update: Update):
    """'PVT - <chat name>' or 'GROUP - <chat name>', for the log lines."""
    chat = update.effective_message.chat
    return f"{'PVT' if chat.type == 'private' else 'GROUP'} - {chat.effective_name}"


def escape_md(name):
    """Escape a name for Telegram (legacy) Markdown."""
    for char in ('_', '*', '`', '['):
        name = name.replace(char, '\\' + char)
    return name


async def reply_chart(update: Update, chart: bytes, message: str):
    """Send a chart with the message as its caption: one request instead of two, when it fits."""
    if len(message.encode('utf-16-le')) // 2 <= MessageLimit.CAPTION_LENGTH:  # Telegram counts UTF-16 units
        await update.message.reply_photo(chart, caption=message, parse_mode='Markdown')
        return
    await update.message.reply_photo(chart)
    await update.message.reply_text(message, parse_mode='Markdown')


async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """True if the sender is an administrator (or the owner) of the chat; always True in private chats."""
    if update.message.chat.type == 'private':
        return True
    try:
        member = await context.bot.get_chat_member(update.message.chat_id, update.message.from_user.id)
    except Exception:
        logger.exception("Could not read the chat member status")
        return False
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
