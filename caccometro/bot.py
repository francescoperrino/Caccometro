import os
import asyncio
import hmac
import logging
from collections import deque
import httpx
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update
from telegram.constants import ChatMemberStatus, MessageLimit
from telegram.error import NetworkError
from telegram.ext import Application, CommandHandler, ExtBot, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import re
from flask import Flask, request, Response

from caccometro.database import (STORING_FORMAT, DISPLAY_FORMAT, ROME_TZ, User, init_database, now_rome, upsert_user,
                      find_user_by_username, add_count, get_count, get_daily_counts, get_rank, get_statistics, get_record,
                      get_all_user_rows, get_constipation_days, list_legacy_users, count_legacy_orphans, link_legacy_username,
                      link_legacy_by_username)
from caccometro.charts import generate_rank_chart, generate_statistics_chart
from caccometro.analysis import analyze_group, analyze_user
from caccometro.formatting import format_group_record, format_user_record

# Load bot info from .env
load_dotenv()
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # also given to set_webhook: Telegram sends it back
RUN_MODE = os.environ.get('RUN_MODE', 'POLLING').upper()

# Enable logging
log_filename = os.environ.get('LOG_FILE', 'caccometro.log')  # the tests point it elsewhere
LOG_MAX_BYTES = 1_000_000  # 1 MB per file...
LOG_BACKUPS = 3            # ...and 3 older files: the logs never take more than about 4 MB
file_handler = RotatingFileHandler(log_filename, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUPS, encoding='utf-8')


def log_handlers(run_mode):
    """The bot log goes to the rotating file; to the console too only when running locally (polling).

    In webhook mode the console is the web server error log: writing there too kept every line twice.
    Crashes before logging is set up (e.g. at import) still reach it.
    """
    if run_mode == 'POLLING':
        return [file_handler, logging.StreamHandler()]
    return [file_handler]


# Log times in Italian time, like every date the bot shows (the server clock runs in UTC)
logging.Formatter.converter = staticmethod(lambda seconds: datetime.fromtimestamp(seconds, ROME_TZ).timetuple())
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO,
                    handlers=log_handlers(RUN_MODE))
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
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


def parse_username_arg(arg):
    """'@mario' -> 'mario'; None if it does not start with @ or is empty."""
    if not arg.startswith('@') or len(arg) < 2:
        return None
    return arg[1:]


def parse_month_arg(arg):
    """'3-2024' or '03-2024' -> '03-2024'; None if it is not a valid month."""
    try:
        return datetime.strptime(arg, '%m-%Y').strftime('%m-%Y')
    except ValueError:
        return None


def parse_year_arg(arg):
    """'2024' -> '2024'; None if it is not a valid year (4 digits, 1970-2100)."""
    if len(arg) == 4 and arg.isdigit() and 1970 <= int(arg) <= 2100:
        return arg
    return None


def parse_date_arg(arg):
    """'DD-MM-YYYY' -> (display date, storing date); raises ValueError if invalid or in the future."""
    parsed_date = datetime.strptime(arg, DISPLAY_FORMAT)
    selected_date = parsed_date.strftime(STORING_FORMAT)
    today = now_rome().strftime(STORING_FORMAT)
    if selected_date > today:
        raise ValueError("La data selezionata è nel futuro.")
    return arg, selected_date


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
            return None, args, f"Formato non valido. Usa: {usage}"
        target = find_user_by_username(chat_id, username)
        if target is None:
            return None, args, (f"Non conosco @{username}: deve scrivere almeno un messaggio nel gruppo "
                                "(oppure rispondi a un suo messaggio).")
        return target, args[1:], None
    replied = update.message.reply_to_message
    if replied is not None and replied.from_user is not None and not replied.from_user.is_bot:
        return register_user(chat_id, replied.from_user), args, None
    return sender, args, None


def record_poop(sender, chat_id):
    """Add one 💩 to today's count of the sender and return the message to reply with."""
    today = now_rome().strftime(STORING_FORMAT)
    _, count = add_count(sender.user_id, today, 1, chat_id)
    return f"Complimenti {escape_md(sender.mention)}, oggi hai fatto 💩 {count} " + ("volte!" if count > 1 else "volta!")


async def reply_chart(update: Update, chart: bytes, message: str):
    """Send a chart with the message as its caption: one request instead of two, when it fits."""
    if len(message.encode('utf-16-le')) // 2 <= MessageLimit.CAPTION_LENGTH:  # Telegram counts UTF-16 units
        await update.message.reply_photo(chart, caption=message, parse_mode='Markdown')
        return
    await update.message.reply_photo(chart)
    await update.message.reply_text(message, parse_mode='Markdown')

def legacy_hint(chat_id):
    """Suffix for 'no data' replies when old username-based history is still waiting to be linked."""
    if list_legacy_users(chat_id):
        return "\n\nℹ️ Ci sono dati storici ancora da collegare: usa /collega."
    return ""


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


async def may_change_counts_of(update: Update, context: ContextTypes.DEFAULT_TYPE, sender, target):
    """Everybody can change their own counts; only the group admins can change the counts of others."""
    if target.user_id == sender.user_id or await is_chat_admin(update, context):
        return True
    await update.message.reply_text("Solo gli admin del gruppo possono modificare i conteggi degli altri.")
    return False


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    sender = register_sender(update)
    logger.info(f"Command received: /start from {sender.mention if sender else None} in {where(update)}")
    init_database(update.message.chat_id)
    await update.message.reply_text("Ciao, sono 🤖 *Caccometro* 🤖.\n"
                                    "Manda 💩 quando hai fatto il tuo dovere.", parse_mode='Markdown')
    logger.info(f"Command /start completed in {where(update)}")

# Wording of the two kinds of period, for the rank and statistics commands
PERIODS = {
    'month': {'name': 'mese', 'parse': parse_month_arg, 'current': '%m-%Y',
              'format_error': "Formato data non valido. Usa MM-YYYY.",
              'of': "del mese", 'in': "Nel mese", 'for': "per il mese"},
    'year': {'name': 'anno', 'parse': parse_year_arg, 'current': '%Y',
             'format_error': "Formato anno non valido. Usa YYYY.",
             'of': "dell'anno", 'in': "Nell'anno", 'for': "per l'anno"},
}
MEDALS = {1: '🥇', 2: '🥈', 3: '🥉'}


def ranked_line(position, name, value):
    """One line of a ranking: a medal and the name in bold for the first three."""
    if position in MEDALS:
        return f"{MEDALS[position]} *{name}*: {value}\n"
    return f"{position}. {name}: {value}\n"


async def period_from_args(update: Update, args, time_period):
    """The period asked for ('MM-YYYY' or 'YYYY'), the current one without arguments.

    Returns None, after telling the user, when the argument is not a valid period.
    """
    period = PERIODS[time_period]
    if not args:
        return now_rome().strftime(period['current'])
    date = period['parse'](args[0])
    if date is None:
        await update.message.reply_text(period['format_error'])
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

    rank = get_rank(update.message.chat_id, time_period, date)
    if not rank:
        await update.message.reply_text(f"{period['in']} {date} non sono state contate 💩." + legacy_hint(update.message.chat_id))
        return

    message = f"Ecco la *classifica {period['of']} {date}*:\n"
    message += "".join(ranked_line(i, escape_md(user.mention), total_count)
                       for i, (user, total_count) in enumerate(rank, start=1))

    daily_counts = get_daily_counts(update.message.chat_id, time_period, date)
    await reply_chart(update, generate_rank_chart(rank, daily_counts, time_period, date), message)
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

    statistics = get_statistics(update.message.chat_id, time_period, date)
    if not statistics:
        await update.message.reply_text(f"Nessuna statistica disponibile {period['for']} {date}." + legacy_hint(update.message.chat_id))
        return

    message = f"*Statistiche {period['for']} {date}*:\n"
    message += "".join(ranked_line(i, escape_md(s['user'].mention),
                                   f"Media: {s['mean']}, Mediana: {s['median']}, Var.: {s['variance']}")
                       for i, s in enumerate(statistics, start=1))

    daily_counts = get_daily_counts(update.message.chat_id, time_period, date)
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
    usage = "/record [@username | io]"
    chat_id = update.message.chat_id
    replied = update.message.reply_to_message
    replies_to_a_person = replied is not None and replied.from_user is not None and not replied.from_user.is_bot
    keyword = context.args[0].lower() if len(context.args) == 1 else None

    if not context.args and not replies_to_a_person:
        # no target at all: the records of the whole group
        rows_by_user, users = get_all_user_rows(chat_id)
        if not rows_by_user:
            await update.message.reply_text("Nessun dato disponibile." + legacy_hint(chat_id))
            return
        board = analyze_group(rows_by_user, now_rome().date())
        names = {user_id: escape_md(user.mention) for user_id, user in users.items()}
        await update.message.reply_text(format_group_record(board, names), parse_mode='Markdown')
        logger.info(f"Command /record (group) completed in {where(update)}")
        return

    if keyword in ("io", "me"):
        target, args, error = sender, [], None
    else:
        target, args, error = resolve_target(update, context.args, sender, usage)
        if error is None and args:
            error = f"Formato non valido. Usa: {usage}"
    if error:
        await update.message.reply_text(error)
        return
    rows = get_record(target.user_id, chat_id)
    if not rows:
        await update.message.reply_text(f"Nessun dato disponibile per {target.mention}." + legacy_hint(update.message.chat_id))
        return
    records = analyze_user(rows, now_rome().date())
    message = format_user_record(escape_md(target.mention), records)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /record completed in {where(update)}")

async def aggiungi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /aggiungi command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /aggiungi from {sender.mention} in {where(update)}")
    usage = "/aggiungi @username DD-MM-YYYY"
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and len(args) != 1:
        error = f"Formato non valido. Usa: {usage}"
    if error:
        await update.message.reply_text(error)
        return
    if not await may_change_counts_of(update, context, sender, target):
        return
    try:
        date, selected_date = parse_date_arg(args[0])
    except ValueError as e:
        await update.message.reply_text(f"Errore: {str(e)}")
        return

    _, new_count = add_count(target.user_id, selected_date, 1, update.message.chat_id)
    await update.message.reply_text(
        f"Il conteggio di {target.mention} nel giorno {date} è stato aggiornato a {new_count} 💩.")
    logger.info(f"Command /aggiungi completed in {where(update)}")

async def togli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /togli command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /togli from {sender.mention} in {where(update)}")
    usage = "/togli @username DD-MM-YYYY"
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and len(args) != 1:
        error = f"Formato non valido. Usa: {usage}"
    if error:
        await update.message.reply_text(error)
        return
    if not await may_change_counts_of(update, context, sender, target):
        return
    try:
        date, selected_date = parse_date_arg(args[0])
    except ValueError as e:
        await update.message.reply_text(f"Errore: {str(e)}")
        return

    old_count, new_count = add_count(target.user_id, selected_date, -1, update.message.chat_id)
    if old_count > 0:
        await update.message.reply_text(
            f"Il conteggio di {target.mention} nel giorno {date} è stato aggiornato a {new_count} 💩.")
    else:
        await update.message.reply_text(
            f"Il conteggio di {target.mention} nel giorno {date} non può essere aggiornato poiché era già 0 💩.")
    logger.info(f"Command /togli completed in {where(update)}")

async def conto_giorno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /conto_giorno command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /conto_giorno from {sender.mention} in {where(update)}")
    usage = "/conto_giorno @username DD-MM-YYYY"
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and len(args) > 1:
        error = f"Formato non valido. Usa: {usage}"
    if error:
        await update.message.reply_text(error)
        return
    if args:
        try:
            date, selected_date = parse_date_arg(args[0])
        except ValueError as e:
            await update.message.reply_text(f"Errore: {str(e)}")
            return
    else:
        selected_date = now_rome().strftime(STORING_FORMAT)

    count = get_count(target.user_id, selected_date, update.message.chat_id)
    if count != 0:
        await update.message.reply_text(f"{target.mention} il giorno {date if args else 'oggi'} hai fatto 💩 {count} {'volte' if count > 1 else 'volta'}.")
    else:
        await update.message.reply_text(f"{target.mention} {'il giorno ' + date if args else 'oggi'} non hai fatto 💩.")
    logger.info(f"Command /conto_giorno completed in {where(update)}")

async def costipazione_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /costipazione command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /costipazione from {sender.mention} in {where(update)}")
    usage = "/costipazione @username"
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and args:
        error = f"Formato non valido. Usa: {usage}"
    if error:
        await update.message.reply_text(error)
        return
    constipation_days = get_constipation_days(target.user_id, update.message.chat_id)
    if constipation_days is not None:
        if constipation_days == 0:
            await update.message.reply_text(f"{target.mention} oggi hai fatto 💩.")
        else:
            await update.message.reply_text(f"{target.mention} non fai 💩 da {constipation_days} {'giorni' if constipation_days > 1 else 'giorno'}.")
    else:
        await update.message.reply_text(f"{target.mention} non ci sono dati sulla costipazione.")
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
            await update.message.reply_text("Non ci sono dati storici da collegare.")
            return
        lines = ["Dati storici ancora da collegare:"]
        for legacy_username, total in legacy:
            match = find_user_by_username(chat_id, legacy_username)
            lines.append(f"• {legacy_username}: {total} 💩" + (f" → {match.mention} (corrispondenza trovata)" if match else ""))
        orphans = count_legacy_orphans(chat_id)
        if orphans:
            lines.append(f"({orphans} registrazioni senza username non si possono collegare.)")
        lines.append("\nGli admin possono usare /collega auto per collegare le corrispondenze, "
                     "oppure rispondere a un messaggio della persona con /collega <username storico>.")
        await update.message.reply_text("\n".join(lines))
        return

    if not await is_chat_admin(update, context):
        await update.message.reply_text("Solo gli admin del gruppo possono collegare i dati storici.")
        return

    # 'auto' is the keyword; an old username that is literally 'auto' can be written as '@auto'
    if len(args) == 1 and args[0] == 'auto':
        linked = link_legacy_by_username(chat_id)
        remaining = list_legacy_users(chat_id)
        lines = []
        if linked:
            lines.append("Collegati:")
            lines += [f"• {legacy_username} → {user.mention} ({days} giorni)" for legacy_username, user, days in linked]
        else:
            lines.append("Nessuna corrispondenza trovata tra lo storico e gli utenti che hanno già scritto nel gruppo.")
        if remaining:
            lines.append("\nDa collegare a mano (rispondi a un messaggio della persona con /collega <username storico>):")
            lines += [f"• {legacy_username}: {total} 💩" for legacy_username, total in remaining]
        await update.message.reply_text("\n".join(lines))
        return

    usage = "/collega <username storico> (in risposta a un messaggio della persona)"
    if len(args) != 1:
        await update.message.reply_text(f"Formato non valido. Usa: {usage}")
        return
    replied = update.message.reply_to_message
    if replied is None or replied.from_user is None or replied.from_user.is_bot:
        await update.message.reply_text(f"Rispondi a un messaggio della persona da collegare. Usa: {usage}")
        return
    legacy_username = args[0].lstrip('@')
    target = register_user(chat_id, replied.from_user)
    days = link_legacy_username(chat_id, legacy_username, target.user_id)
    if days == 0:
        await update.message.reply_text(f"Nessun dato storico trovato per «{legacy_username}» (già collegato o inesistente).")
    else:
        await update.message.reply_text(f"Collegati {days} giorni di dati storici di «{legacy_username}» a {target.mention}.")
    logger.info(f"Command /collega completed in {where(update)}")


# Messages handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for processing messages."""
    if not update.message:
        logger.info(f"Update type not managed")
        return
    sender = register_sender(update)
    if sender is None:
        logger.info("Message without a usable sender (channel post, anonymous admin or bot): ignored.")
        return
    chat_id = update.message.chat_id
    if update.message.text:
        text: str = update.message.text.lower().strip()
        response: str = ""
        if BOT_USERNAME and BOT_USERNAME.lower() in text:
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
        logger.info(f"Update type not managed")

# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for logging errors."""
    if update:
        logger.error(f'Update "{update.update_id}" caused error "{context.error}"', exc_info=context.error)
    else:
        logger.error(f'Error: "{context.error}"', exc_info=context.error)

class CachedMeBot(ExtBot):
    """ExtBot that asks Telegram 'who am I?' (getMe) only once per process.

    The webhook initializes and shuts down the application for every update, and Bot.initialize()
    calls getMe each time: one extra outbound request per message, and one more chance to hit a
    proxy error. The answer never changes, so it is kept after the first success (a failed call is
    not cached and is simply tried again).
    """

    async def get_me(self, *args, **kwargs):
        if self._bot_user is not None:
            return self._bot_user
        return await super().get_me(*args, **kwargs)


class RetryingRequest(HTTPXRequest):
    """HTTPXRequest that tries a request again when the connection to Telegram fails.

    Outgoing requests sometimes fail at once with a proxy error (503) and work a moment later.
    Only errors raised before the request reached Telegram are retried: after a timeout or a
    dropped connection the message may already have been delivered, and a retry would send it twice.
    """
    RETRYABLE = (httpx.ProxyError, httpx.ConnectError)
    RETRY_DELAYS = (1, 2)  # seconds before the 2nd and the 3rd attempt

    async def do_request(self, *args, **kwargs):
        for delay in self.RETRY_DELAYS:
            try:
                return await super().do_request(*args, **kwargs)
            except NetworkError as e:
                if not isinstance(e.__cause__, self.RETRYABLE):
                    raise
                logger.warning(f"Telegram request failed ({e}), new attempt in {delay} s")
                await asyncio.sleep(delay)
        return await super().do_request(*args, **kwargs)


# Create the Application instance (same connection pools as Application.builder().token(...) would use)
application = Application.builder().bot(CachedMeBot(
    BOT_TOKEN,
    request=RetryingRequest(connection_pool_size=256),
    get_updates_request=HTTPXRequest(connection_pool_size=1),
)).build()

# Add handlers
application.add_handler(CommandHandler('start', start_command))
application.add_handler(CommandHandler('classifica_mese', classifica_mese_command))
application.add_handler(CommandHandler('classifica_anno', classifica_anno_command))
application.add_handler(CommandHandler('statistiche_mese', statistiche_mese_command))
application.add_handler(CommandHandler('statistiche_anno', statistiche_anno_command))
application.add_handler(CommandHandler('record', record_command))
application.add_handler(CommandHandler('aggiungi', aggiungi_command))
application.add_handler(CommandHandler('togli', togli_command))
application.add_handler(CommandHandler('conto_giorno', conto_giorno_command))
application.add_handler(CommandHandler('costipazione', costipazione_command))
application.add_handler(CommandHandler('collega', collega_command))

# Messages
application.add_handler(MessageHandler(filters.ALL, handle_message))

# Errors
application.add_error_handler(error)

app = Flask(__name__)

# Telegram sends an update again when the webhook fails or answers late: remember the last ones
# so that a 💩 is never counted twice. Kept in memory: enough, as a resend comes within minutes.
SEEN_UPDATE_IDS = deque(maxlen=500)

@app.route('/webhook', methods=['POST'])
async def webhook():
    """This function receives the update from Telegram and passes it to the library."""
    # Only Telegram knows the secret: without it anybody could send fake updates
    received_secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    if not WEBHOOK_SECRET or not hmac.compare_digest(received_secret, WEBHOOK_SECRET):
        logger.warning("Webhook call without the right secret token: refused.")
        return Response('forbidden', status=403)
    logger.info("Webhook received...")
    try:
        # 1. Start the application
        await application.initialize()

        # 2. Process the update as before
        update = Update.de_json(request.get_json(force=True), application.bot)
        if update.update_id in SEEN_UPDATE_IDS:
            logger.warning(f'Update "{update.update_id}" already processed: ignored.')
            return Response('ok', status=200)
        SEEN_UPDATE_IDS.append(update.update_id)
        await application.process_update(update)

        # Respond to Telegram that everything is ok
        return Response('ok', status=200)
    
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return Response('error', status=500)
    
    finally:
        # 3. Terminate the application
        # This "turns off" the bot and cleans up resources,
        # both in case of success (try) and in case of error (except).
        await application.shutdown()

@app.route('/')
def index():
    """Welcome page, useful for testing if the web app works."""
    return 'Ciao! Sono il Caccometro Bot. Il mio webhook è pronto.'

def main():
    """Run the bot in polling mode (local development); in webhook mode the web server imports `app` (see wsgi.py)."""
    if RUN_MODE == 'POLLING':
        logger.info("Starting bot in POLLING mode...")
        # run_polling retries network errors by itself and stops on Ctrl+C: no restart loop needed
        # (a loop restarted it on a closed event loop and failed again at once, forever)
        application.run_polling(allowed_updates=[Update.MESSAGE])