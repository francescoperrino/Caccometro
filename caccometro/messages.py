"""Handler of plain messages: counts the 💩 and 🚽 sent as text or sticker."""
import logging
import random
import re
import time

from telegram import Update
from telegram.ext import ContextTypes

from caccometro import config, maps
from caccometro.chat import escape_md, register_sender, reply_charts
from caccometro.config import ROME_TZ, STORING_FORMAT, now_rome
from caccometro.conquest import WINDOW_SECONDS, cell_of, holdings, mention_of
from caccometro.database import (add_count, conquer, get_language, get_record, get_users, migrate_chat,
                                 open_conquest_window)
from caccometro.formatting import format_streak_trophy, poop_sentence
from caccometro.i18n import tr
from caccometro.menus import set_chat_menu
from caccometro.trophies import new_streak_trophy

logger = logging.getLogger(__name__)


def record_poop(sender, chat_id, sent_at=None):
    """Add one 💩 to the day the message was sent (Italian time) and return the message to reply with.

    sent_at is the aware datetime of the Telegram message, so a late-processed update still counts on its own day.
    The first 💩 of a day that completes a multiple of STREAK_STEP consecutive days also announces a trophy.
    The 💩 also opens the conquest window of the sender, and the reply reminds to send a location.
    """
    sent = now_rome() if sent_at is None else sent_at.astimezone(ROME_TZ)
    today = sent.date()
    _, count = add_count(sender.user_id, today.strftime(STORING_FORMAT), 1, chat_id)
    open_conquest_window(sender.user_id, int(time.time() if sent_at is None else sent_at.timestamp()), chat_id)
    response = poop_sentence(escape_md(sender.mention), sent.hour, count) + "\n" + tr("💩 oggi: {count}").format(count=count)
    if count == 1:
        streak = new_streak_trophy(get_record(sender.user_id, chat_id), today)
        if streak is not None:
            response += "\n\n" + format_streak_trophy(streak)
    return response + "\n\n" + tr("📍 Manda la posizione entro 15 minuti per conquistare la zona!")


def record_conquest(sender, chat_id, location, sent_at):
    """Conquer the tile of a location sent within the window of the sender's last 💩.

    Returns the reply and, for the zoom image, the conquest history and the users of the chat
    (None, None without an open window).
    """
    result = conquer(chat_id, sender.user_id, int(sent_at.timestamp()), location.latitude, location.longitude,
                     cell_of(location.latitude, location.longitude), WINDOW_SECONDS)
    if result is None:
        return tr("Prima la 💩, poi la conquista 😏"), None, None
    previous, history = result
    king_before = holdings(history[:-1])[1]
    counts, king = holdings(history)
    users = get_users(chat_id)
    name, total = escape_md(sender.mention), counts[sender.user_id]
    if previous is None:
        response = tr("🚩 {name} conquista una nuova zona! Zone: {total}").format(name=name, total=total)
    elif previous == sender.user_id:
        response = tr("🏠 {name} difende la sua zona. Zone: {total}").format(name=name, total=total)
    else:
        response = tr("⚔️ {name} ruba una zona a {owner}! Zone: {total}").format(
            name=name, owner=escape_md(mention_of(users, previous)), total=total)
    if king != king_before:
        response += "\n" + tr("👑 {name} è il nuovo re della collina!").format(name=escape_md(mention_of(users, king)))
    return response, history, users


async def handle_migration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """A basic group became a supergroup: Telegram gave it a new chat ID, so the database follows it."""
    old_chat_id = update.message.migrate_from_chat_id
    new_chat_id = update.message.chat_id
    if old_chat_id is None:  # the twin message sent in the old chat: a second chance if the first one failed
        old_chat_id, new_chat_id = new_chat_id, update.message.migrate_to_chat_id
        if new_chat_id is None:
            return
    result = migrate_chat(old_chat_id, new_chat_id)
    if result == 'both_have_data':
        logger.warning(f"Chat {old_chat_id} became {new_chat_id}, but the legacy history of both databases "
                       "would collide: left untouched.")
    else:
        logger.info(f"Chat {old_chat_id} became {new_chat_id}: {result}.")
    language = get_language(new_chat_id)
    if language:  # a menu set with /language belongs to the old chat ID
        await set_chat_menu(context.bot, new_chat_id, language, group=True)


# Messages handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for processing messages."""
    if not update.message:
        logger.info("Update type not managed")
        return
    sender = register_sender(update)
    if sender is None:
        logger.info("Message without a usable sender (channel post, anonymous admin or bot): ignored.")
        return
    chat_id = update.message.chat_id
    if update.message.text:
        text: str = update.message.text.lower().strip()
        response: str = ""
        if config.BOT_USERNAME and config.BOT_USERNAME.lower() in text:
            response = tr("💬 Cosa vuoi dirmi?")
        elif "💩" in text or "🚽" in text:
            response = record_poop(sender, chat_id, update.message.date)
        elif re.search(r'\brun\b', text):
            response = "🙄 " + random.choice([
                tr("{name} cazzo scrivi *Run*, funziono solo con i comandi specifici e non quelli che ti inventi tu."),
                tr("{name}, *Run* non è un comando. Funziono solo con quelli veri, non con quelli che ti inventi tu."),
                tr("{name}, ma sei serio? *Run*?! Guarda il menu dei comandi, poi riprova."),
            ]).format(name=escape_md(sender.mention))
        if response:
            await update.message.reply_text(response, parse_mode='Markdown')
    elif update.message.sticker:
        emoji = update.message.sticker.emoji # Get the emoji from sticker
        if emoji == "💩" or emoji == "🚽":
            response = record_poop(sender, chat_id, update.message.date)
            await update.message.reply_text(response, parse_mode='Markdown')
    elif update.message.location:
        response, history, users = record_conquest(sender, chat_id, update.message.location, update.message.date)
        await reply_charts(update, [history and maps.render(maps.zoom_map, history, users)], response)
    else:
        logger.info("Update type not managed")
