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
    """Tell whether the sender may change the counts of a person; everybody can change their own, only the group admins those of others.

    Replies to the sender when not allowed.

    Args:
        update (Update): the incoming message.
        context (ContextTypes.DEFAULT_TYPE): holds `context.args`, the arguments of the command.
        sender (User): who wrote the command.
        target (User): whose counts are changed.

    Returns:
        bool: True if allowed.
    """
    if target.user_id == sender.user_id or await is_chat_admin(update, context):
        return True
    await update.message.reply_text(tr("🔒 Solo gli admin del gruppo possono modificare i conteggi degli altri."))
    return False


async def _change_count_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command, delta):
    """Shared body of /add_poop and /remove_poop.

    Args:
        update (Update): the incoming message.
        context (ContextTypes.DEFAULT_TYPE): holds `context.args`, the arguments of the command.
        command (str): the English name of the command, for the log line.
        delta (int): +1 to add a 💩, -1 to remove one.
    """
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
    """/add_poop: add 1 💩 on a day.

    Args:
        update (Update): the incoming message.
        context (ContextTypes.DEFAULT_TYPE): holds `context.args`, the arguments of the command.
    """
    await _change_count_command(update, context, 'add_poop', 1)


async def remove_poop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/remove_poop: remove 1 💩 on a day.

    Args:
        update (Update): the incoming message.
        context (ContextTypes.DEFAULT_TYPE): holds `context.args`, the arguments of the command.
    """
    await _change_count_command(update, context, 'remove_poop', -1)


async def day_count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/day_count: the 💩 of a person on a day (today without a date).

    Args:
        update (Update): the incoming message.
        context (ContextTypes.DEFAULT_TYPE): holds `context.args`, the arguments of the command.
    """
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
    """/last_poop: the days since the last 💩 of a person.

    Args:
        update (Update): the incoming message.
        context (ContextTypes.DEFAULT_TYPE): holds `context.args`, the arguments of the command.
    """
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
