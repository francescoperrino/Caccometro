"""Handler of plain messages: counts the 💩 and 🚽 sent as text or sticker."""
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from caccometro import config
from caccometro.chat import escape_md, register_sender, where
from caccometro.config import STORING_FORMAT, now_rome
from caccometro.database import add_count

logger = logging.getLogger(__name__)


def record_poop(sender, chat_id):
    """Add one 💩 to today's count of the sender and return the message to reply with."""
    today = now_rome().strftime(STORING_FORMAT)
    _, count = add_count(sender.user_id, today, 1, chat_id)
    return f"Complimenti {escape_md(sender.mention)}, oggi hai fatto 💩 {count} " + ("volte!" if count > 1 else "volta!")


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
            response = record_poop(sender, chat_id)
        elif re.search(r'\brun\b', text):
            response = f"{escape_md(sender.mention)} cazzo scrivi *Run*, funziono solo con i comandi specifici e non quelli che ti inventi tu."
        if response:
            await update.message.reply_text(response, parse_mode='Markdown')
            # Only answered messages are logged, never their text: the bot reads every group message
            logger.info(f"{sender.mention} in {where(update)}: Risposta: {response}")
    elif update.message.sticker:
        emoji = update.message.sticker.emoji # Get the emoji from sticker
        if emoji == "💩" or emoji == "🚽":
            response = record_poop(sender, chat_id)
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"{sender.mention} in {where(update)}: Sticker | Risposta: {response}")
    else:
        logger.info("Update type not managed")
