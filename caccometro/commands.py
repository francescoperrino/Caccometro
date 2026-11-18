"""Command handlers: parse the arguments, read or change the data, reply."""
import logging
import re
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from caccometro import __version__, i18n
from caccometro.analysis import FORECAST_WINDOW_DAYS, analyze_group, analyze_user, forecast_totals, period_statistics
from caccometro.charts import generate_rank_chart, generate_statistics_chart
from caccometro.chat import escape_md, is_chat_admin, register_sender, register_user, reply_chart, where
from caccometro.config import DISPLAY_FORMAT, MONTH_NAMES, STORING_FORMAT, now_rome, period_bounds
from caccometro.i18n import MONTHS, tr
from caccometro.database import (init_database, find_user_by_username, add_count, get_count, get_daily_counts,
                                 get_daily_counts_between,
                                 get_rank, get_users, get_record, get_all_user_rows, get_constipation_days,
                                 list_legacy_users, count_legacy_orphans, link_legacy_username, link_legacy_by_username,
                                 set_language)
from caccometro.formatting import bold, format_group_record, format_group_trophies, format_user_record, format_user_trophies
from caccometro.trophies import trophies_by_user

logger = logging.getLogger(__name__)


def parse_username_arg(arg):
    """'@mario' -> 'mario'; None if it does not start with @ or is empty."""
    if not arg.startswith('@') or len(arg) < 2:
        return None
    return arg[1:]


MIN_YEAR, MAX_YEAR = 1970, 2100  # the years accepted in the arguments of the commands


# '-', '/' and '.' are the same separator; the year has 2 digits (20YY) or 4; leading zeros are optional
MONTH_ARG = re.compile(r'([0-9]{1,2})[-/.]([0-9]{2}|[0-9]{4})')
MONTH_NAME_ARG = re.compile(r'([a-z]+)(?: ([0-9]{2}|[0-9]{4}))?')  # 'marzo 2026', 'marzo 26' or 'marzo' (this year)
DATE_ARG = re.compile(r'([0-9]{1,2})[-/.]([0-9]{1,2})(?:[-/.]([0-9]{2}|[0-9]{4}))?')  # without the year: this year
# Words accepted in every chat, whatever its language
MONTH_NUMBERS = {name.lower(): number for names in (MONTH_NAMES, *MONTHS.values())
                 for number, name in enumerate(names) if number}
DAYS_AGO = {'oggi': 0, 'today': 0, 'ieri': 1, 'yesterday': 1}


def _year_of(text):
    """'26' -> 2026, '2026' -> 2026."""
    return 2000 + int(text) if len(text) == 2 else int(text)


def parse_month_arg(arg):
    """'3-2024', '03/24', '03.2024', 'marzo 2024' or 'march 2024' -> '03-2024'; None if it is not a valid month (years 1970-2100)."""
    arg = arg.strip().lower()
    match = MONTH_ARG.fullmatch(arg)
    if match is not None:
        month, year = int(match.group(1)), _year_of(match.group(2))
    else:
        match = MONTH_NAME_ARG.fullmatch(arg)
        if match is None or match.group(1) not in MONTH_NUMBERS:
            return None
        month = MONTH_NUMBERS[match.group(1)]
        year = _year_of(match.group(2)) if match.group(2) else now_rome().year
    return f'{month:02d}-{year}' if 1 <= month <= 12 and MIN_YEAR <= year <= MAX_YEAR else None


def parse_year_arg(arg):
    """'2024' or '24' -> '2024'; None if it is not a valid year (2 or 4 digits, 1970-2100)."""
    if re.fullmatch(r'([0-9]{2}|[0-9]{4})', arg) and MIN_YEAR <= _year_of(arg) <= MAX_YEAR:
        return str(_year_of(arg))
    return None


def parse_date_arg(arg):
    """'5/3/26', '05.03.2026', '5.3', 'oggi', 'yesterday'... -> ('05-03-2026', '2026-03-05').

    Raises ValueError, with the message for the user, if invalid, before 1970 or in the future.
    """
    today = now_rome().date()
    word, match = arg.lower(), DATE_ARG.fullmatch(arg)
    try:
        if word in DAYS_AGO:
            selected_date = today - timedelta(days=DAYS_AGO[word])
        else:
            year = _year_of(match.group(3)) if match.group(3) else today.year
            selected_date = datetime(year, int(match.group(2)), int(match.group(1))).date()
    except (AttributeError, ValueError):  # no match, or a day that does not exist
        raise ValueError(tr("Data non valida. Esempi: 05-03-2026, 5/3/26, 5.3 (anno corrente), oggi, ieri.")) from None
    if selected_date > today:
        raise ValueError(tr("La data selezionata è nel futuro."))
    if selected_date.year < MIN_YEAR:
        raise ValueError(tr("L'anno deve essere dal {year} in poi.").format(year=MIN_YEAR))
    # isoformat, not strftime: on Linux '%Y' does not pad the year with zeros
    return selected_date.strftime(DISPLAY_FORMAT), selected_date.isoformat()


def resolve_target(update: Update, args, sender, usage):
    """Work out whose data a command refers to.

    Order: an explicit '@username' as first argument (it must belong to a user the bot has already
    seen), then the author of the message being replied to, then the sender.
    Returns (target, remaining_args, error_message); target is None when there is an error.
    """
    chat_id = update.message.chat_id
    if args and args[0].startswith('@'):
        username = parse_username_arg(args[0])
        if username is None:
            return None, args, invalid_format(usage)
        target = find_user_by_username(chat_id, username)
        if target is None:
            return None, args, tr("Non conosco @{username}: deve scrivere almeno un messaggio nel gruppo "
                                  "(oppure rispondi a un suo messaggio).").format(username=username)
        return target, args[1:], None
    replied = replied_person(update)
    if replied is not None:
        return register_user(chat_id, replied), args, None
    return sender, args, None


def invalid_format(usage):
    """The reply to arguments that do not fit the command."""
    return tr("Formato non valido. Usa: {usage}").format(usage=usage)


def replied_person(update: Update):
    """The Telegram user of the message being replied to, or None when the reply is not to a person.

    A bot is not a person. Inside a forum topic every message is a reply to the message that created
    the topic: that is not a reply to its author either.
    """
    replied = update.message.reply_to_message
    if replied is None or replied.forum_topic_created is not None or replied.from_user is None or replied.from_user.is_bot:
        return None
    return replied.from_user


def resolve_optional_target(update: Update, context: ContextTypes.DEFAULT_TYPE, sender, usage):
    """Target of /record and /trofei: io, @username or a reply. Returns (target, error); no target and no error means the group."""
    if len(context.args) == 1 and context.args[0].lower() in ("io", "me"):
        return sender, None
    if not context.args and replied_person(update) is None:
        return None, None
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and args:
        error = invalid_format(usage)
    return target, error


def legacy_hint(chat_id):
    """Suffix for 'no data' replies when old username-based history is still waiting to be linked."""
    if list_legacy_users(chat_id):
        return "\n\n" + tr("ℹ️ Ci sono dati storici ancora da collegare: usa /collega.")
    return ""


async def may_change_counts_of(update: Update, context: ContextTypes.DEFAULT_TYPE, sender, target):
    """Everybody can change their own counts; only the group admins can change the counts of others."""
    if target.user_id == sender.user_id or await is_chat_admin(update, context):
        return True
    await update.message.reply_text(tr("Solo gli admin del gruppo possono modificare i conteggi degli altri."))
    return False


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /start from {sender.mention} in {where(update)}")
    init_database(update.message.chat_id)
    await update.message.reply_text(tr("Ciao, sono 🤖 *Caccometro* 🤖.\n"
                                       "Manda 💩 quando hai fatto il tuo dovere.\n"
                                       "_Versione {version}_\n\n"
                                       "🇬🇧 English: /language en").format(version=__version__), parse_mode='Markdown')
    logger.info(f"Command /start completed in {where(update)}")

# The two kinds of period of the rank and statistics commands; their sentences are chosen with `month and ... or ...`
PERIODS = {
    'month': {'name': 'mese', 'parse': parse_month_arg, 'current': '%m-%Y'},
    'year': {'name': 'anno', 'parse': parse_year_arg, 'current': '%Y'},
}
MEDALS = {1: '🥇', 2: '🥈', 3: '🥉'}


def ranked_line(position, name, value):
    """One line of a ranking: a medal and the name in bold for the first three."""
    if position in MEDALS:
        return f"{MEDALS[position]} {bold(name)}: {value}\n"
    return f"{position}. {name}: {value}\n"


async def period_from_args(update: Update, args, time_period):
    """The period asked for ('MM-YYYY' or 'YYYY'), the current one without arguments.

    Returns None, after telling the user, when the argument is not a valid period.
    """
    period = PERIODS[time_period]
    if not args:
        return now_rome().strftime(period['current'])
    date = period['parse'](' '.join(args))  # joined: 'marzo 2026' arrives as two arguments
    if date is None:
        await update.message.reply_text(
            tr("Formato data non valido. Usa MM-YYYY (anche 3/2026, 03.26 o marzo 2026).") if time_period == 'month'
            else tr("Formato anno non valido. Usa YYYY (anche 26)."))
    return date


async def rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE, time_period):
    """/classifica_mese and /classifica_anno: total 💩 per person in the period, with a chart."""
    sender = register_sender(update)
    if sender is None:
        return
    period = PERIODS[time_period]
    command = f"classifica_{period['name']}"
    logger.info(f"Command received: /{command} from {sender.mention} in {where(update)}")
    date = await period_from_args(update, context.args, time_period)
    if date is None:
        return

    month = time_period == 'month'
    rank = get_rank(update.message.chat_id, time_period, date)
    if not rank:
        empty = tr("Nel mese {date} non sono state contate 💩.") if month else tr("Nell'anno {date} non sono state contate 💩.")
        await update.message.reply_text(empty.format(date=date) + legacy_hint(update.message.chat_id))
        return

    # Ongoing period: forecast of the total at its end, next to each count
    today = now_rome().date()
    start_period, end_period = period_bounds(time_period, date)
    forecast = {}
    if start_period <= today.isoformat() <= end_period:
        recent = get_daily_counts_between(update.message.chat_id,
                                          (today - timedelta(days=FORECAST_WINDOW_DAYS - 1)).isoformat(),
                                          today.isoformat())
        forecast = forecast_totals({user.user_id: total for user, total in rank}, recent, today, end_period)

    message = (tr("🏆 *Classifica del mese {date}*") if month else tr("🏆 *Classifica dell'anno {date}*")).format(date=date) + "\n"
    if forecast:
        message += (tr("_💩 finora → previsione a fine mese_") if month else tr("_💩 finora → previsione a fine anno_")) + "\n"
    message += "\n" + "".join(ranked_line(i, escape_md(user.mention),
                                         f"{total_count} 💩" + (f" → {forecast[user.user_id]}" if forecast else ""))
                              for i, (user, total_count) in enumerate(rank, start=1))

    daily_counts = get_daily_counts(update.message.chat_id, time_period, date)
    await reply_chart(update, generate_rank_chart(rank, daily_counts, time_period, date, forecast), message)
    logger.info(f"Command /{command} completed in {where(update)}")

async def statistics_command(update: Update, context: ContextTypes.DEFAULT_TYPE, time_period):
    """/statistiche_mese and /statistiche_anno: mean, median and variance per person, with a chart."""
    sender = register_sender(update)
    if sender is None:
        return
    period = PERIODS[time_period]
    command = f"statistiche_{period['name']}"
    logger.info(f"Command received: /{command} from {sender.mention} in {where(update)}")
    date = await period_from_args(update, context.args, time_period)
    if date is None:
        return

    chat_id = update.message.chat_id
    daily_counts = get_daily_counts(chat_id, time_period, date)
    statistics = period_statistics(daily_counts, get_users(chat_id), *period_bounds(time_period, date),
                                   now_rome().date())
    month = time_period == 'month'
    if not statistics:
        empty = (tr("Nessuna statistica disponibile per il mese {date}.") if month
                 else tr("Nessuna statistica disponibile per l'anno {date}."))
        await update.message.reply_text(empty.format(date=date) + legacy_hint(update.message.chat_id))
        return

    message = (tr("📊 *Statistiche del mese {date}*") if month else tr("📊 *Statistiche dell'anno {date}*")).format(date=date)
    message += "\n" + tr("💩 al giorno: media · mediana · varianza") + "\n\n"
    message += "".join(ranked_line(i, escape_md(s['user'].mention),
                                   f"{s['mean']:.2f} · {s['median']:.1f} · {s['variance']:.2f}")
                       for i, s in enumerate(statistics, start=1))

    await reply_chart(update, generate_statistics_chart(statistics, daily_counts, time_period, date), message)
    logger.info(f"Command /{command} completed in {where(update)}")

async def classifica_mese_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_mese command."""
    await rank_command(update, context, 'month')

async def classifica_anno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_anno command."""
    await rank_command(update, context, 'year')

async def statistiche_mese_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /statistiche_mese command."""
    await statistics_command(update, context, 'month')

async def statistiche_anno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /statistiche_anno command."""
    await statistics_command(update, context, 'year')

async def record_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /record command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /record from {sender.mention} in {where(update)}")
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
            await update.message.reply_text(tr("Nessun dato disponibile.") + legacy_hint(chat_id))
            return
        board = analyze_group(rows_by_user, now_rome().date())
        names = {user_id: escape_md(user.mention) for user_id, user in users.items()}
        await update.message.reply_text(format_group_record(board, names), parse_mode='Markdown')
        logger.info(f"Command /record (group) completed in {where(update)}")
        return

    rows = get_record(target.user_id, chat_id)
    if not rows:
        await update.message.reply_text(tr("Nessun dato disponibile per {name}.").format(name=target.mention)
                                        + legacy_hint(update.message.chat_id))
        return
    records = analyze_user(rows, now_rome().date())
    message = format_user_record(escape_md(target.mention), records)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /record completed in {where(update)}")

async def trofei_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /trofei command: the trophies of the group, or of one person (io, @username or a reply)."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /trofei from {sender.mention} in {where(update)}")
    usage = tr("/trofei [@username | io]")
    chat_id = update.message.chat_id
    target, error = resolve_optional_target(update, context, sender, usage)
    if error:
        await update.message.reply_text(error)
        return

    rows_by_user, users = get_all_user_rows(chat_id)
    today = now_rome().date()
    trophies = trophies_by_user(rows_by_user, today)
    if target is None:
        names = {user_id: escape_md(user.mention) for user_id, user in users.items()}
        message = format_group_trophies(trophies, names)
    else:
        rows = rows_by_user.get(target.user_id)
        current_streak = analyze_user(rows, today).status.streak_days if rows and any(c > 0 for _, c in rows) else 0
        message = format_user_trophies(escape_md(target.mention), trophies.get(target.user_id), current_streak)
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /trofei completed in {where(update)}")

async def change_count_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command, delta):
    """Shared body of /aggiungi (delta +1) and /togli (delta -1)."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /{command} from {sender.mention} in {where(update)}")
    usage = tr("/aggiungi @username DD-MM-YYYY") if delta > 0 else tr("/togli @username DD-MM-YYYY")
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and len(args) != 1:
        error = invalid_format(usage)
    if error:
        await update.message.reply_text(error)
        return
    if not await may_change_counts_of(update, context, sender, target):
        return
    try:
        date, selected_date = parse_date_arg(args[0])
    except ValueError as e:
        await update.message.reply_text(tr("Errore: {error}").format(error=e))
        return

    old_count, new_count = add_count(target.user_id, selected_date, delta, update.message.chat_id)
    logger.info(f"Count changed by {sender.mention} in {where(update)}: /{command} {target.mention} "
                f"{selected_date} {old_count} -> {new_count}")
    if delta < 0 and old_count == 0:
        await update.message.reply_text(
            tr("Il conteggio di {name} nel giorno {date} non può essere aggiornato poiché era già 0 💩.")
            .format(name=target.mention, date=date))
    else:
        await update.message.reply_text(
            tr("Il conteggio di {name} nel giorno {date} è stato aggiornato a {count} 💩.")
            .format(name=target.mention, date=date, count=new_count))
    logger.info(f"Command /{command} completed in {where(update)}")

async def aggiungi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /aggiungi command."""
    await change_count_command(update, context, 'aggiungi', 1)

async def togli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /togli command."""
    await change_count_command(update, context, 'togli', -1)

async def conto_giorno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /conto_giorno command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /conto_giorno from {sender.mention} in {where(update)}")
    usage = tr("/conto_giorno @username DD-MM-YYYY")
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and len(args) > 1:
        error = invalid_format(usage)
    if error:
        await update.message.reply_text(error)
        return
    if args:
        try:
            date, selected_date = parse_date_arg(args[0])
        except ValueError as e:
            await update.message.reply_text(tr("Errore: {error}").format(error=e))
            return
        day = tr("il giorno {date}").format(date=date)
    else:
        selected_date = now_rome().strftime(STORING_FORMAT)
        day = tr("oggi")

    count = get_count(target.user_id, selected_date, update.message.chat_id)
    if count == 0:
        reply = tr("{name} {day} non hai fatto 💩.")
    else:
        reply = tr("{name} {day} hai fatto 💩 {count} volte.") if count > 1 else tr("{name} {day} hai fatto 💩 {count} volta.")
    await update.message.reply_text(reply.format(name=target.mention, day=day, count=count))
    logger.info(f"Command /conto_giorno completed in {where(update)}")

async def costipazione_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /costipazione command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /costipazione from {sender.mention} in {where(update)}")
    usage = tr("/costipazione @username")
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and args:
        error = invalid_format(usage)
    if error:
        await update.message.reply_text(error)
        return
    days = get_constipation_days(target.user_id, update.message.chat_id)
    if days is None:
        reply = tr("{name} non ci sono dati sulla costipazione.")
    elif days == 0:
        reply = tr("{name} oggi hai fatto 💩.")
    else:
        reply = tr("{name} non fai 💩 da {days} giorni.") if days > 1 else tr("{name} non fai 💩 da {days} giorno.")
    await update.message.reply_text(reply.format(name=target.mention, days=days))
    logger.info(f"Command /costipazione completed in {where(update)}")

async def collega_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /collega command: link the old username-based history to Telegram users.

    /collega                    list the history that is still to be linked (everybody)
    /collega auto               link every old username that matches a known user (admins)
    /collega <old username>     as a reply to a message of the person: link that history to them (admins)
    """
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /collega from {sender.mention} in {where(update)}")
    chat_id = update.message.chat_id
    args = context.args

    if not args:
        legacy = list_legacy_users(chat_id)
        if not legacy:
            await update.message.reply_text(tr("Non ci sono dati storici da collegare."))
            return
        lines = [tr("Dati storici ancora da collegare:")]
        for legacy_username, total in legacy:
            match = find_user_by_username(chat_id, legacy_username)
            lines.append(f"• {legacy_username}: {total} 💩"
                         + (tr(" → {name} (corrispondenza trovata)").format(name=match.mention) if match else ""))
        orphans = count_legacy_orphans(chat_id)
        if orphans:
            lines.append(tr("({orphans} registrazioni senza username non si possono collegare.)").format(orphans=orphans))
        lines.append("\n" + tr("Gli admin possono usare /collega auto per collegare le corrispondenze, "
                               "oppure rispondere a un messaggio della persona con /collega <username storico>."))
        await update.message.reply_text("\n".join(lines))
        return

    if not await is_chat_admin(update, context):
        await update.message.reply_text(tr("Solo gli admin del gruppo possono collegare i dati storici."))
        return

    # 'auto' is the keyword; an old username that is literally 'auto' can be written as '@auto'
    if len(args) == 1 and args[0] == 'auto':
        linked = link_legacy_by_username(chat_id)
        for legacy_username, user, days in linked:
            logger.info(f"History linked by {sender.mention} in {where(update)}: "
                        f"{legacy_username} -> {user.mention}, {days} days")
        remaining = list_legacy_users(chat_id)
        lines = []
        if linked:
            lines.append(tr("Collegati:"))
            lines += [tr("• {username} → {name} ({days} giorni)").format(username=legacy_username, name=user.mention, days=days)
                      for legacy_username, user, days in linked]
        else:
            lines.append(tr("Nessuna corrispondenza trovata tra lo storico e gli utenti che hanno già scritto nel gruppo."))
        if remaining:
            lines.append("\n" + tr("Da collegare a mano (rispondi a un messaggio della persona con /collega <username storico>):"))
            lines += [f"• {legacy_username}: {total} 💩" for legacy_username, total in remaining]
        await update.message.reply_text("\n".join(lines))
        return

    usage = tr("/collega <username storico> (in risposta a un messaggio della persona)")
    if len(args) != 1:
        await update.message.reply_text(invalid_format(usage))
        return
    replied = replied_person(update)
    if replied is None:
        await update.message.reply_text(tr("Rispondi a un messaggio della persona da collegare. Usa: {usage}").format(usage=usage))
        return
    legacy_username = args[0].lstrip('@')
    target = register_user(chat_id, replied)
    days = link_legacy_username(chat_id, legacy_username, target.user_id)
    logger.info(f"History linked by {sender.mention} in {where(update)}: {legacy_username} -> {target.mention}, {days} days")
    if days == 0:
        await update.message.reply_text(tr("Nessun dato storico trovato per «{username}» (già collegato o inesistente).")
                                        .format(username=legacy_username))
    else:
        await update.message.reply_text(tr("Collegati {days} giorni di dati storici di «{username}» a {name}.")
                                        .format(days=days, username=legacy_username, name=target.mention))
    logger.info(f"Command /collega completed in {where(update)}")


async def lingua_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /lingua command: show the language of the chat or, for the admins, change it (/lingua en)."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /lingua from {sender.mention} in {where(update)}")
    language = context.args[0].lower() if len(context.args) == 1 else None
    if language not in i18n.LANGUAGES:
        await update.message.reply_text(tr("La lingua di questa chat è {name}. Per cambiarla: /lingua it oppure /lingua en.")
                                        .format(name=i18n.LANGUAGES[i18n.current()]))
        return
    if not await is_chat_admin(update, context):
        await update.message.reply_text(tr("Solo gli admin del gruppo possono cambiare la lingua."))
        return
    set_language(update.message.chat_id, language)
    i18n.use(language)
    logger.info(f"Language changed by {sender.mention} in {where(update)}: {language}")
    await update.message.reply_text(tr("Da ora parlo italiano 🇮🇹"))
    logger.info(f"Command /lingua completed in {where(update)}")
