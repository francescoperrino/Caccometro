import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import pytz
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
from flask import Flask, request, Response

from database import (STORING_FORMAT, DISPLAY_FORMAT, CHARTS_FOLDER, User, init_database, upsert_user,
                      find_user_by_username, get_count, update_count, get_rank, get_statistics, get_record,
                      get_constipation_days, list_legacy_users, count_legacy_orphans, link_legacy_username,
                      link_legacy_by_username)
from utils import generate_rank_chart, generate_statistics_chart, analyze_user_record

# Enable logging
log_filename = "caccometro.log"
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler(log_filename, encoding='utf-8'),
                        logging.StreamHandler()
                    ])
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Load bot info from .env
load_dotenv()
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
RUN_MODE = os.environ.get('RUN_MODE', 'POLLING').upper()

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
    today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
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
    today = datetime.now(pytz.timezone("Europe/Rome")).strftime(STORING_FORMAT)
    count = get_count(sender.user_id, today, chat_id) + 1
    update_count(sender.user_id, today, count, chat_id)
    return f"Complimenti {escape_md(sender.mention)}, oggi hai fatto 💩 {count} " + ("volte!" if count > 1 else "volta!")


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


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    sender = register_sender(update)
    logger.info(f"Command received: /start from {sender.mention if sender else None} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    init_database(update.message.chat_id)
    await update.message.reply_text("Ciao, sono 🤖 *Caccometro* 🤖.\n"
                                    "Manda 💩 quando hai fatto il tuo dovere.", parse_mode='Markdown')
    logger.info(f"Command /start completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def classifica_mese_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_mese command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /classifica_mese from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        date = parse_month_arg(args[0])
        if date is None:
            await update.message.reply_text("Formato data non valido. Usa MM-YYYY.")
            return
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        date = now.strftime("%m-%Y")

    rank = get_rank(update.message.chat_id, 'month', date)
    if not rank:
        await update.message.reply_text(f"Nel mese {date} non sono state contate 💩." + legacy_hint(update.message.chat_id))
        return

    message = f"Ecco la *classifica del mese {date}*:\n"
    for i, (user, total_count) in enumerate(rank, start=1):
        escaped_name = escape_md(user.mention)
        if i == 1:
            message += f"🥇 *{escaped_name}*: {total_count}\n"
        elif i == 2:
            message += f"🥈 *{escaped_name}*: {total_count}\n"
        elif i == 3:
            message += f"🥉 *{escaped_name}*: {total_count}\n"
        else:
            message += f"{i}. {escaped_name}: {total_count}\n"

    generate_rank_chart(rank, update.message.chat_id, 'month', date)

    date_parts = date.split('-')
    saving_date = f"{date_parts[1]}_{date_parts[0]}"

    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{saving_date}_chart.png'), 'rb') as chart:
        await update.message.reply_photo(chart)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /classifica_mese completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def classifica_anno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_anno command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /classifica_anno from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        year = parse_year_arg(args[0])
        if year is None:
            await update.message.reply_text("Formato anno non valido. Usa YYYY.")
            return
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        year = now.strftime("%Y")

    rank = get_rank(update.message.chat_id, 'year', year)
    if not rank:
        await update.message.reply_text(f'Nell\'anno {year} non sono state contate 💩.' + legacy_hint(update.message.chat_id))
        return

    message = f"Ecco la *classifica dell\'anno {year}*:\n"
    for i, (user, total_count) in enumerate(rank, start=1):
        escaped_name = escape_md(user.mention)
        if i == 1:
            message += f"🥇 *{escaped_name}*: {total_count}\n"
        elif i == 2:
            message += f"🥈 *{escaped_name}*: {total_count}\n"
        elif i == 3:
            message += f"🥉 *{escaped_name}*: {total_count}\n"
        else:
            message += f"{i}. {escaped_name}: {total_count}\n"

    generate_rank_chart(rank, update.message.chat_id, 'year', year)

    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{year}_chart.png'), 'rb') as chart:
        await update.message.reply_photo(chart)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /classifica_anno completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def statistiche_mese_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /statistiche_mese command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /statistiche_mese from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        date = parse_month_arg(args[0])
        if date is None:
            await update.message.reply_text("Formato data non valido. Usa MM-YYYY.")
            return
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        date = now.strftime("%m-%Y")

    statistics = get_statistics(update.message.chat_id, 'month', date)
    if not statistics:
        await update.message.reply_text(f"Nessuna statistica disponibile per il mese {date}." + legacy_hint(update.message.chat_id))
        return

    message = f"*Statistiche per il mese {date}*:\n"
    for i, statistic in enumerate(statistics, start=1):
        escaped_name = escape_md(statistic['user'].mention)
        mean = str(statistic['mean'])
        median = str(statistic['median'])
        variance = str(statistic['variance'])
        if i == 1:
            message += f"🥇 *{escaped_name}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        elif i == 2:
            message += f"🥈 *{escaped_name}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        elif i == 3:
            message += f"🥉 *{escaped_name}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        else:
            message += f"{i}. {escaped_name}: Media: {mean}, Mediana: {median}, Var.: {variance}\n"

    generate_statistics_chart(statistics, update.message.chat_id, 'month', date)

    date_parts = date.split('-')
    saving_date = f"{date_parts[1]}_{date_parts[0]}"
    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{saving_date}_stats.png'), 'rb') as stats:
        await update.message.reply_photo(stats)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /statistica_mese completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def statistiche_anno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /statistiche_anno command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /statistiche_anno from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        year = parse_year_arg(args[0])
        if year is None:
            await update.message.reply_text("Formato anno non valido. Usa YYYY.")
            return
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        year = now.strftime("%Y")

    statistics = get_statistics(update.message.chat_id, 'year', year)
    if not statistics:
        await update.message.reply_text(f"Nessuna statistica disponibile per l\'anno {year}." + legacy_hint(update.message.chat_id))
        return

    message = f"*Statistiche per l\'anno {year}*:\n"
    for i, statistic in enumerate(statistics, start=1):
        escaped_name = escape_md(statistic['user'].mention)
        mean = str(statistic['mean'])
        median = str(statistic['median'])
        variance = str(statistic['variance'])
        if i == 1:
            message += f"🥇 *{escaped_name}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        elif i == 2:
            message += f"🥈 *{escaped_name}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        elif i == 3:
            message += f"🥉 *{escaped_name}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        else:
            message += f"{i}. {escaped_name}: Media: {mean}, Mediana: {median}, Var.: {variance}\n"

    generate_statistics_chart(statistics, update.message.chat_id, 'year', year)

    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{year}_stats.png'), 'rb') as stats:
        await update.message.reply_photo(stats)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /statistica_anno completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def record_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /record command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /record from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    usage = "/record @username"
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and args:
        error = f"Formato non valido. Usa: {usage}"
    if error:
        await update.message.reply_text(error)
        return
    chat_id = update.message.chat_id
    rows = get_record(target.user_id, chat_id)
    if not rows:
        await update.message.reply_text(f"Nessun dato disponibile per {target.mention}." + legacy_hint(update.message.chat_id))
        return
    record_data = analyze_user_record(rows)

    def volte(n):
        return 'volte' if n > 1 else 'volta'

    lines = [
        f"📊 *Record per {escape_md(target.mention)}* 📊\n",
        f"🥵 Hai fatto 💩 {record_data['max_daily_count']} {volte(record_data['max_daily_count'])} il {record_data['max_days']}.",
    ]

    # Monthly records exclude the current month: they do not exist until a month has been completed.
    if record_data['max_monthly_count'] is not None:
        max_in = 'nei mesi' if ', ' in record_data['max_months'] else 'nel mese'
        min_in = 'nei mesi' if ', ' in record_data['min_months'] else 'nel mese'
        lines.append(f"🤩 Hai fatto 💩 {record_data['max_monthly_count']} {volte(record_data['max_monthly_count'])} {max_in} {record_data['max_months']}.")
        lines.append(f"😭 Hai fatto solo 💩 {record_data['min_monthly_count']} {volte(record_data['min_monthly_count'])} {min_in} {record_data['min_months']}.")
    else:
        lines.append("🗓️ I record mensili saranno disponibili dopo il primo mese completo.")

    lines.append(f"🥳 Hai fatto 💩 per {record_data['max_streak_days']} giorni consecutivi ({record_data['max_streak_period']}).")
    lines.append(f"🫣 Hai fatto 💩 {record_data['max_streak_count']} {volte(record_data['max_streak_count'])} in una serie di giorni consecutivi ({record_data['max_streak_count_period']}).")
    if record_data['max_gap_days'] > 0:
        lines.append(f"🤢 Non hai fatto 💩 per {record_data['max_gap_days']} giorni consecutivi ({record_data['max_gap_period']}).")
    else:
        lines.append("🤢 Non ci sono ancora giorni senza 💩 tra la prima e l'ultima registrazione.")

    message = "\n".join(lines)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /record completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def aggiungi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /aggiungi command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /aggiungi from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    usage = "/aggiungi @username DD-MM-YYYY"
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and len(args) != 1:
        error = f"Formato non valido. Usa: {usage}"
    if error:
        await update.message.reply_text(error)
        return
    try:
        date, selected_date = parse_date_arg(args[0])
    except ValueError as e:
        await update.message.reply_text(f"Errore: {str(e)}")
        return

    chat_id = update.message.chat_id
    count = get_count(target.user_id, selected_date, chat_id)
    update_count(target.user_id, selected_date, count + 1, chat_id)
    await update.message.reply_text(
        f"Il conteggio di {target.mention} nel giorno {date} è stato aggiornato a {count + 1} 💩.")
    logger.info(f"Command /aggiungi completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def togli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /togli command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /togli from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    usage = "/togli @username DD-MM-YYYY"
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and len(args) != 1:
        error = f"Formato non valido. Usa: {usage}"
    if error:
        await update.message.reply_text(error)
        return
    try:
        date, selected_date = parse_date_arg(args[0])
    except ValueError as e:
        await update.message.reply_text(f"Errore: {str(e)}")
        return

    chat_id = update.message.chat_id
    count = get_count(target.user_id, selected_date, chat_id)
    if count > 0:
        update_count(target.user_id, selected_date, count - 1, chat_id)
        await update.message.reply_text(
            f"Il conteggio di {target.mention} nel giorno {date} è stato aggiornato a {count - 1} 💩.")
    else:
        await update.message.reply_text(
            f"Il conteggio di {target.mention} nel giorno {date} non può essere aggiornato poiché era già 0 💩.")
    logger.info(f"Command /togli completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def conto_giorno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /conto_giorno command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /conto_giorno from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
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
        selected_date = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)

    count = get_count(target.user_id, selected_date, update.message.chat_id)
    if count != 0:
        await update.message.reply_text(f"{target.mention} il giorno {date if args else 'oggi'} hai fatto 💩 {count} {'volte' if count > 1 else 'volta'}.")
    else:
        await update.message.reply_text(f"{target.mention} {'il giorno ' + date if args else 'oggi'} non hai fatto 💩.")
    logger.info(f"Command /conto_giorno completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def costipazione_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /costipazione command."""
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /costipazione from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
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
    logger.info(f"Command /costipazione completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def collega_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /collega command: link the old username-based history to Telegram users.

    /collega                    list the history that is still to be linked (everybody)
    /collega auto               link every old username that matches a known user (admins)
    /collega <old username>     as a reply to a message of the person: link that history to them (admins)
    """
    sender = register_sender(update)
    if sender is None:
        return
    logger.info(f"Command received: /collega from {sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
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
    logger.info(f"Command /collega completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")


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
        if not text: # Check for empty message
            logger.info(f"{sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}: Messaggio vuoto.")
            return # Exit the function, no further processing needed
        if BOT_USERNAME and BOT_USERNAME.lower() in text:
            response = "Cosa vuoi dirmi?"
        elif "💩" in text or "🚽" in text:
            response = record_poop(sender, chat_id)
        elif re.search(r'\brun\b', text):
            response = f"{escape_md(sender.mention)} cazzo scrivi *Run*, funziono solo con i comandi specifici e non quelli che ti inventi tu."
        if response:
            await update.message.reply_text(response, parse_mode='Markdown')
        # Log for debugging
        logger.info(f"{sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}: {text} | Risposta: {response}")
    elif update.message.sticker:
        emoji = update.message.sticker.emoji # Get the emoji from sticker
        if emoji == "💩" or emoji == "🚽":
            response = record_poop(sender, chat_id)
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"{sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}: Sticker  | Risposta: {response}")
        else:
            logger.info(f"{sender.mention} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}: Sticker {emoji} | Emoji non gestita.")
    else:
        logger.info(f"Update type not managed")

# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for logging errors."""
    if update:
        logger.error(f'Update "{update.update_id}" caused error "{context.error}"', exc_info=context.error)
    else:
        logger.error(f'Error: "{context.error}"', exc_info=context.error)

# Create the Application instance
application = Application.builder().token(BOT_TOKEN).build()

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

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def webhook():
    """This function receives the update from Telegram and passes it to the library."""
    logger.info("Webhook received...")
    try:
        # 1. Start the application)
        await application.initialize()

        # 2. Process the update as before
        update = Update.de_json(request.get_json(force=True), application.bot)
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

# Main function to handle bot interactions
if __name__ == '__main__':

    # Run the bot in the selected mode
    if RUN_MODE == 'WEBHOOK':
        logger.info("Starting bot in WEBHOOK mode...")

        pass

    elif RUN_MODE == 'POLLING':
        logger.info("Starting bot in POLLING mode...")

        while True:
            try:
                application.run_polling(allowed_updates=[Update.MESSAGE])
                break

            except KeyboardInterrupt:
                logger.info("Bot stopped by user.")
                break

            except Exception as e:
                logger.error(f"Error in polling: {e}")