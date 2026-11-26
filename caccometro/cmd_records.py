"""/records and /trophies: of the group, or of one person (io, @username or a reply)."""
from telegram import Update
from telegram.ext import ContextTypes

from caccometro.analysis import analyze_group, analyze_user, record_places
from caccometro.arguments import resolve_optional_target
from caccometro.chat import escape_md, legacy_hint, register_sender
from caccometro.config import now_rome
from caccometro.database import get_all_user_rows, get_record, get_timed_conquests
from caccometro.formatting import format_group_record, format_group_trophies, format_user_record, format_user_trophies
from caccometro.i18n import tr
from caccometro.trophies import trophies_by_user


async def records_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /records command."""
    sender = register_sender(update)
    if sender is None:
        return
    usage = tr("/record [@username | io]")
    chat_id = update.message.chat_id
    target, error = resolve_optional_target(update, context, sender, usage)
    if error:
        await update.message.reply_text(error)
        return

    if target is None:
        # no target at all: the records of the whole group
        rows_by_user, users = get_all_user_rows(chat_id)
        if not rows_by_user:
            await update.message.reply_text(tr("🤷 Nessun dato disponibile.") + legacy_hint(chat_id))
            return
        board = analyze_group(rows_by_user, now_rome().date())
        names = {user_id: escape_md(user.mention) for user_id, user in users.items()}
        await update.message.reply_text(format_group_record(board, names), parse_mode='Markdown')
        return

    rows = get_record(target.user_id, chat_id)
    if not rows:
        await update.message.reply_text(tr("🤷 Nessun dato disponibile per {name}.").format(name=target.mention)
                                        + legacy_hint(update.message.chat_id))
        return
    today = now_rome().date()
    people = {user_id: analyze_user(user_rows, today) for user_id, user_rows in get_all_user_rows(chat_id)[0].items()
              if any(c > 0 for _, c in user_rows)}
    message = format_user_record(escape_md(target.mention), analyze_user(rows, today), record_places(target.user_id, people))

    await update.message.reply_text(message, parse_mode='Markdown')


async def trophies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /trophies command: the trophies of the group, or of one person (io, @username or a reply)."""
    sender = register_sender(update)
    if sender is None:
        return
    usage = tr("/trofei [@username | io]")
    chat_id = update.message.chat_id
    target, error = resolve_optional_target(update, context, sender, usage)
    if error:
        await update.message.reply_text(error)
        return

    rows_by_user, users = get_all_user_rows(chat_id)
    today = now_rome().date()
    trophies = trophies_by_user(rows_by_user, today, get_timed_conquests(chat_id))
    if target is None:
        names = {user_id: escape_md(user.mention) for user_id, user in users.items()}
        message = format_group_trophies(trophies, names)
    else:
        rows = rows_by_user.get(target.user_id)
        current_streak = analyze_user(rows, today).status.streak_days if rows and any(c > 0 for _, c in rows) else 0
        message = format_user_trophies(escape_md(target.mention), trophies.get(target.user_id), current_streak)
    await update.message.reply_text(message, parse_mode='Markdown')
