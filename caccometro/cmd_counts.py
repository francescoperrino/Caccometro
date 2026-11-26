"""/add_poop, /remove_poop, /day_count and /last_poop: the counts of one person."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from caccometro.arguments import date_from_arg, target_from_args
from caccometro.chat import is_chat_admin, register_sender, where
from caccometro.config import STORING_FORMAT, now_rome
from caccometro.database import add_count, get_count, get_days_since_last_poop
from caccometro.formatting import change_count_sentence, day_count_sentence, last_poop_sentence
from caccometro.i18n import tr

logger = logging.getLogger(__name__)


async def _may_change_counts_of(update: Update, context: ContextTypes.DEFAULT_TYPE, sender, target):
    """Everybody can change their own counts; only the group admins can change the counts of others."""
    if target.user_id == sender.user_id or await is_chat_admin(update, context):
        return True
    await update.message.reply_text(tr("🔒 Solo gli admin del gruppo possono modificare i conteggi degli altri."))
    return False


async def _change_count_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command, delta):
    """Shared body of /add_poop (delta +1) and /remove_poop (delta -1)."""
    sender = register_sender(update)
    if sender is None:
        return
    usage = tr("/aggiungi_cacca @username DD-MM-YYYY") if delta > 0 else tr("/togli_cacca @username DD-MM-YYYY")
    found = await target_from_args(update, context.args, sender, usage, counts=(1,))
    if found is None:
        return
    target, args = found
    if not await _may_change_counts_of(update, context, sender, target):
        return
    parsed = await date_from_arg(update, args[0])
    if parsed is None:
        return
    date, selected_date = parsed

    old_count, new_count = add_count(target.user_id, selected_date, delta, update.message.chat_id)
    logger.info(f"Count changed by {sender.mention} in {where(update)}: /{command} {target.mention} "
                f"{selected_date} {old_count} -> {new_count}")
    if delta < 0 and old_count == 0:
        await update.message.reply_text(
            tr("⚠️ Il conteggio di {name} nel giorno {date} non può essere aggiornato poiché era già 0 💩.")
            .format(name=target.mention, date=date))
    else:
        await update.message.reply_text(change_count_sentence(target.mention, date, new_count, delta))


async def add_poop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /add_poop command."""
    await _change_count_command(update, context, 'add_poop', 1)


async def remove_poop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /remove_poop command."""
    await _change_count_command(update, context, 'remove_poop', -1)


async def day_count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /day_count command."""
    sender = register_sender(update)
    if sender is None:
        return
    usage = tr("/conto_giorno @username DD-MM-YYYY")
    found = await target_from_args(update, context.args, sender, usage, counts=(0, 1))
    if found is None:
        return
    target, args = found
    if args:
        parsed = await date_from_arg(update, args[0])
        if parsed is None:
            return
        date, selected_date = parsed
        day = tr("il giorno {date}").format(date=date)
    else:
        selected_date = now_rome().strftime(STORING_FORMAT)
        day = tr("oggi")

    count = get_count(target.user_id, selected_date, update.message.chat_id)
    await update.message.reply_text(day_count_sentence(target.mention, day, count))


async def last_poop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /last_poop command."""
    sender = register_sender(update)
    if sender is None:
        return
    usage = tr("/ultima_cacca @username")
    found = await target_from_args(update, context.args, sender, usage, counts=(0,))
    if found is None:
        return
    target, _ = found
    days = get_days_since_last_poop(target.user_id, update.message.chat_id)
    await update.message.reply_text(last_poop_sentence(target.mention, days))
