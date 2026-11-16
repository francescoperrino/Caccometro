"""Handler of plain messages: counts the 💩 and 🚽 sent as text or sticker."""
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from caccometro import config
from caccometro.chat import escape_md, register_sender, where
from caccometro.config import ROME_TZ, STORING_FORMAT, now_rome
from caccometro.database import add_count, get_record
from caccometro.formatting import format_streak_trophy
from caccometro.trophies import new_streak_trophy

logger = logging.getLogger(__name__)


def record_poop(sender, chat_id, sent_at=None):
    """Add one 💩 to the day the message was sent (Italian time) and return the message to reply with.

    sent_at is the aware datetime of the Telegram message, so a late-processed update still counts on its own day.
    The first 💩 of a day that completes a multiple of STREAK_STEP consecutive days also announces a trophy.
    """
    today = now_rome().date() if sent_at is None else sent_at.astimezone(ROME_TZ).date()
    _, count = add_count(sender.user_id, today.strftime(STORING_FORMAT), 1, chat_id)
    response = f"Complimenti {escape_md(sender.mention)}, oggi hai fatto 💩 {count} " + ("volte!" if count > 1 else "volta!")
    if count == 1:
        streak = new_streak_trophy(get_record(sender.user_id, chat_id), today)
        if streak is not None:
            response += "\n\n" + format_streak_trophy(streak)
    return response


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
            response = "Cosa vuoi dirmi?"
        elif "💩" in text or "🚽" in text:
            response = record_poop(sender, chat_id, update.message.date)
        elif re.search(r'\brun\b', text):
            response = f"{escape_md(sender.mention)} cazzo scrivi *Run*, funziono solo con i comandi specifici e non quelli che ti inventi tu."
        if response:
            await update.message.reply_text(response, parse_mode='Markdown')
            # Only answered messages are logged, never their text: the bot reads every group message
            logger.info(f"{sender.mention} in {where(update)}: Risposta: {response}")
    elif update.message.sticker:
        emoji = update.message.sticker.emoji # Get the emoji from sticker
        if emoji == "💩" or emoji == "🚽":
            response = record_poop(sender, chat_id, update.message.date)
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"{sender.mention} in {where(update)}: Sticker | Risposta: {response}")
    else:
        logger.info("Update type not managed")
