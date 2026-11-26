"""Helpers shared by the commands and the message handler: users, replies, permissions."""
import logging

from telegram import InputMediaPhoto, Update
from telegram.constants import ChatMemberStatus, MessageLimit
from telegram.ext import ContextTypes

from caccometro import i18n
from caccometro.database import get_language, list_legacy_users, upsert_user
from caccometro.i18n import tr
from caccometro.model import User

logger = logging.getLogger(__name__)

# Telegram can take more than the default 5 seconds to answer an upload (an album of maps took 7):
# a read timeout is not retried, so the reply would count as failed although it arrived
PHOTO_READ_TIMEOUT = 20


def _display_name_of(tg_user):
    """Name shown for users without a username: their full name, falling back to the numeric ID.

    Args:
        tg_user (telegram.User): the Telegram user.

    Returns:
        str: the name.
    """
    return tg_user.full_name or str(tg_user.id)


def register_user(chat_id, tg_user):
    """Store the current username and name of a Telegram user.

    Args:
        chat_id (int): the Telegram chat.
        tg_user (telegram.User): the Telegram user.

    Returns:
        User: the user as stored.
    """
    user = User(tg_user.id, tg_user.username, _display_name_of(tg_user))
    upsert_user(chat_id, user.user_id, user.username, user.display_name)
    return user


def register_sender(update: Update):
    """Record the sender of the message in the users table; the replies follow the language of the chat.

    Args:
        update (Update): the incoming message.

    Returns:
        User: the sender; None when there is no usable sender (channel posts, anonymous admins, bots).
    """
    tg_user = update.message.from_user if update.message else None
    if tg_user is None or tg_user.is_bot:
        return None
    i18n.use(get_language(update.message.chat_id))
    return register_user(update.message.chat_id, tg_user)


def where(update: Update):
    """Say where an update comes from, for the log lines.

    Args:
        update (Update): the incoming message.

    Returns:
        str: 'PVT - <chat name>' or 'GROUP - <chat name>'.
    """
    chat = update.effective_message.chat
    return f"{'PVT' if chat.type == 'private' else 'GROUP'} - {chat.effective_name}"


def escape_md(name):
    """Escape a name for Telegram (legacy) Markdown.

    Args:
        name (str): the name.

    Returns:
        str: the name with a backslash before each of _ * ` [.
    """
    for char in ('_', '*', '`', '['):
        name = name.replace(char, '\\' + char)
    return name


def _fits_caption(message):
    """Tell whether a message fits a photo caption (Telegram counts UTF-16 units).

    Args:
        message (str): the message.

    Returns:
        bool: True if it fits.
    """
    return len(message.encode('utf-16-le')) // 2 <= MessageLimit.CAPTION_LENGTH


async def reply_chart(update: Update, chart: bytes, message: str):
    """Send a chart with the message as its caption: one request instead of two, when it fits.

    Args:
        update (Update): the incoming message.
        chart (bytes): the image.
        message (str): the text, in Markdown; it goes in a separate message when it is too long for a caption.
    """
    if _fits_caption(message):
        await update.message.reply_photo(chart, caption=message, parse_mode='Markdown', read_timeout=PHOTO_READ_TIMEOUT)
        return
    await update.message.reply_photo(chart, read_timeout=PHOTO_READ_TIMEOUT)
    await update.message.reply_text(message, parse_mode='Markdown')


async def reply_charts(update: Update, charts, message: str):
    """Send the charts that could be drawn with the message: an album when there are several, the text alone when there are none.

    Args:
        update (Update): the incoming message.
        charts (list): the images; the None ones are skipped.
        message (str): the text, in Markdown.
    """
    charts = [chart for chart in charts if chart]
    if not charts:
        await update.message.reply_text(message, parse_mode='Markdown')
    elif len(charts) == 1:
        await reply_chart(update, charts[0], message)
    else:
        caption = _fits_caption(message)
        if not caption:
            await update.message.reply_text(message, parse_mode='Markdown')
        await update.message.reply_media_group([
            InputMediaPhoto(chart, caption=message if caption and i == 0 else None, parse_mode='Markdown')
            for i, chart in enumerate(charts)], read_timeout=PHOTO_READ_TIMEOUT)


async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tell whether the sender is an administrator (or the owner) of the chat.

    Args:
        update (Update): the incoming message.
        context (ContextTypes.DEFAULT_TYPE): holds the bot, used to ask Telegram.

    Returns:
        bool: True for an administrator; always True in private chats; False when Telegram cannot tell.
    """
    if update.message.chat.type == 'private':
        return True
    try:
        member = await context.bot.get_chat_member(update.message.chat_id, update.message.from_user.id)
    except Exception:
        logger.exception("Could not read the chat member status")
        return False
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


def legacy_hint(chat_id):
    """Suffix for 'no data' replies when old username-based history is still waiting to be linked.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        str: the hint, empty when there is nothing to link.
    """
    if list_legacy_users(chat_id):
        return "\n\n" + tr("ℹ️ Ci sono dati storici ancora da collegare: usa /collega_storico.")
    return ""
