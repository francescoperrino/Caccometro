import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
from flask import Flask, request, Response

from database import STORING_FORMAT, DISPLAY_FORMAT, CHARTS_FOLDER, init_database, get_count, update_count, get_rank, get_statistics, get_record, get_constipation_days
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

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /start from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    init_database(update.message.chat_id)
    await update.message.reply_text("Ciao, sono 🤖 *Caccometro* 🤖.\n"
                                    "Manda 💩 quando hai fatto il tuo dovere.", parse_mode='Markdown')
    logger.info(f"Command /start completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def classifica_mese_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_mese command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /classifica_mese from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        try:
            month, year = args[0].split('-')
            date = f"{month}-{year}"
        except ValueError:
            await update.message.reply_text("Formato data non valido. Usa MM-YYYY.")
            return
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        date = now.strftime("%m-%Y")

    rank = get_rank(update.message.chat_id, 'month', date)
    if not rank:
        await update.message.reply_text(f"Nel mese {date} non sono state contate 💩.")
        return

    message = f"Ecco la *classifica del mese {date}*:\n"
    for i, (username, total_count) in enumerate(rank, start=1):
        escaped_username = username.replace('_', '\\_')  # Escape underscores
        if i == 1:
            message += f"🥇 *@{escaped_username}*: {total_count}\n"
        elif i == 2:
            message += f"🥈 *@{escaped_username}*: {total_count}\n"
        elif i == 3:
            message += f"🥉 *@{escaped_username}*: {total_count}\n"
        else:
            message += f"{i}. @{escaped_username}: {total_count}\n"

    generate_rank_chart(rank, update.message.chat_id, 'month', date)

    date_parts = date.split('-')
    saving_date = f"{date_parts[1]}_{date_parts[0]}"

    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{saving_date}_chart.png'), 'rb') as chart:
        await update.message.reply_photo(chart)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /classifica_mese completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def classifica_anno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_anno command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /classifica_anno from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        year = args[0]
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        year = now.strftime("%Y")

    rank = get_rank(update.message.chat_id, 'year', year)
    if not rank:
        await update.message.reply_text(f'Nell\'anno {year} non sono state contate 💩.')
        return

    message = f"Ecco la *classifica dell\'anno {year}*:\n"
    for i, (username, total_count) in enumerate(rank, start=1):
        escaped_username = username.replace('_', '\\_')  # Escape underscores
        if i == 1:
            message += f"🥇 *@{escaped_username}*: {total_count}\n"
        elif i == 2:
            message += f"🥈 *@{escaped_username}*: {total_count}\n"
        elif i == 3:
            message += f"🥉 *@{escaped_username}*: {total_count}\n"
        else:
            message += f"{i}. @{escaped_username}: {total_count}\n"

    generate_rank_chart(rank, update.message.chat_id, 'year', year)

    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{year}_chart.png'), 'rb') as chart:
        await update.message.reply_photo(chart)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /classifica_anno completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def statistiche_mese_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /statistiche_mese command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /statistiche_mese from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        try:
            month, year = args[0].split('-')
            date = f"{month}-{year}"
        except ValueError:
            await update.message.reply_text("Formato data non valido. Usa MM-YYYY.")
            return
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        date = now.strftime("%m-%Y")

    statistics = get_statistics(update.message.chat_id, 'month', date)
    if not statistics:
        await update.message.reply_text(f"Nessuna statistica disponibile per il mese {date}.")
        return

    message = f"*Statistiche per il mese {date}*:\n"
    for i, statistic in enumerate(statistics, start=1):
        escaped_username = statistic['username'].replace('_', '\\_')  # Escape underscores
        mean = str(statistic['mean'])
        median = str(statistic['median'])
        variance = str(statistic['variance'])
        if i == 1:
            message += f"🥇 *@{escaped_username}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        elif i == 2:
            message += f"🥈 *@{escaped_username}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        elif i == 3:
            message += f"🥉 *@{escaped_username}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        else:
            message += f"{i}. @{escaped_username}: Media: {mean}, Mediana: {median}, Var.: {variance}\n"

    generate_statistics_chart(statistics, update.message.chat_id, 'month', date)

    date_parts = date.split('-')
    saving_date = f"{date_parts[1]}_{date_parts[0]}"
    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{saving_date}_stats.png'), 'rb') as stats:
        await update.message.reply_photo(stats)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /statistica_mese completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def statistiche_anno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /statistiche_anno command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /statistiche_anno from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        year = args[0]
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        year = now.strftime("%Y")

    statistics = get_statistics(update.message.chat_id, 'year', year)
    if not statistics:
        await update.message.reply_text(f"Nessuna statistica disponibile per l\'anno {year}.")
        return

    message = f"*Statistiche per l\'anno {year}*:\n"
    for i, statistic in enumerate(statistics, start=1):
        escaped_username = statistic['username'].replace('_', '\\_')  # Escape underscores
        mean = str(statistic['mean'])
        median = str(statistic['median'])
        variance = str(statistic['variance'])
        if i == 1:
            message += f"🥇 *@{escaped_username}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        elif i == 2:
            message += f"🥈 *@{escaped_username}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        elif i == 3:
            message += f"🥉 *@{escaped_username}*: Media: {mean}, Mediana: {median}, Var.: {variance}\n"
        else:
            message += f"{i}. @{escaped_username}: Media: {mean}, Mediana: {median}, Var.: {variance}\n"

    generate_statistics_chart(statistics, update.message.chat_id, 'year', year)

    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{year}_stats.png'), 'rb') as stats:
        await update.message.reply_photo(stats)

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /statistica_anno completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def record_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /record command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /record from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        username = args[0][1:]
    else:
        username = update.message.from_user.username
    
    chat_id = update.message.chat_id
    rows = get_record(username, chat_id)
    
    if not rows:
        await update.message.reply_text(f"Nessun dato disponibile per @{username}.")
        return
    
    record_data = analyze_user_record(rows)
    
    message = (
        f"📊 *Record per @{username}* 📊\n\n"
        f"🥵 Hai fatto 💩 {record_data['max_daily_count']} {'volte' if record_data['max_daily_count'] > 1 else 'volta'} il {record_data['max_days']}.\n"
        f"🤩 Hai fatto 💩 {record_data['max_monthly_count']} {'volte' if record_data['max_monthly_count'] > 1 else 'volta'} {'nei mesi' if len(record_data['max_months']) > 1 else 'nel mese'} {record_data['max_months']}.\n"
        f"😭 Hai fatto solo 💩 {record_data['min_monthly_count']} {'volte' if record_data['min_monthly_count'] > 1 else 'volta'} {'nei mesi' if len(record_data['min_months']) > 1 else 'nel mese'} {record_data['min_months']}.\n"
        f"🥳 Hai fatto 💩 per {record_data['max_streak_days']} giorni consecutivi ({record_data['max_streak_period']}).\n"
        f"🫣 Hai fatto 💩 {record_data['max_streak_count']} {'volte' if record_data['max_streak_count'] > 1 else 'volta'} in {record_data['max_streak_days']} {'giorni consecutivi' if record_data['max_streak_days'] > 1 else 'un giorno'} ({record_data['max_streak_count_period']}).\n"
        f"🤢 Non hai fatto 💩 per {record_data['max_gap_days']} giorni consecutivi ({record_data['max_gap_period']})."
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Command /record completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def aggiungi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /aggiungi command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /aggiungi from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    
    if len(args) != 1 and len(args) != 2:
        await update.message.reply_text("Formato non valido. Usa: /aggiungi @username DD-MM-YYYY")
        return
    
    if len(args) == 1:
        try:
            username = update.message.from_user.username
            date = args[0]
            parsed_date = datetime.strptime(date, DISPLAY_FORMAT)
            selected_date = parsed_date.strftime(STORING_FORMAT)
            today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
            if selected_date > today:
                raise ValueError("La data selezionata è nel futuro.")
        except ValueError as e:
            await update.message.reply_text(f"Errore: {str(e)}")
            return
    
    if len(args) == 2:
        if not args[0].startswith('@'):
            await update.message.reply_text("Formato non valido. Usa: /aggiungi @username DD-MM-YYYY")
            return
        try:
            username = args[0][1:]
            date = args[1]
            parsed_date = datetime.strptime(date, DISPLAY_FORMAT)
            selected_date = parsed_date.strftime(STORING_FORMAT)
            today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
            if selected_date > today:
                raise ValueError("La data selezionata è nel futuro.")
        except ValueError as e:
            await update.message.reply_text(f"Errore: {str(e)}")
            return

    count = get_count(username, selected_date, update.message.chat_id)
    update_count(username, selected_date, count + 1, update.message.chat_id)
    await update.message.reply_text(
        f"Il conteggio di @{username} nel giorno {date} è stato aggiornato a {count + 1} 💩.")
    logger.info(f"Command /aggiungi completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def togli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /togli command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /togli from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    
    if len(args) != 1 and len(args) != 2:
        await update.message.reply_text("Formato non valido. Usa: /togli @username DD-MM-YYYY")
        return
    
    if len(args) == 1:
        try:
            username = update.message.from_user.username
            date = args[0]
            parsed_date = datetime.strptime(date, DISPLAY_FORMAT)
            selected_date = parsed_date.strftime(STORING_FORMAT)
            today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
            if selected_date > today:
                raise ValueError("La data selezionata è nel futuro.")
        except ValueError as e:
            await update.message.reply_text(f"Errore: {str(e)}")
            return
    
    if len(args) == 2:
        if not args[0].startswith('@'):
            await update.message.reply_text("Formato non valido. Usa: /togli @username DD-MM-YYYY")
            return
        try:
            username = args[0][1:]
            date = args[1]
            parsed_date = datetime.strptime(date, DISPLAY_FORMAT)
            selected_date = parsed_date.strftime(STORING_FORMAT)
            today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
            if selected_date > today:
                raise ValueError("La data selezionata è nel futuro.")
        except ValueError as e:
            await update.message.reply_text(f"Errore: {str(e)}")
            return

    count = get_count(username, selected_date, update.message.chat_id)
    if count > 0:
        update_count(username, selected_date, count - 1, update.message.chat_id)
        await update.message.reply_text(
            f"Il conteggio di @{username} nel giorno {date} è stato aggiornato a {count - 1} 💩.")
    else:
        await update.message.reply_text(
            f"Il conteggio di @{username} nel giorno {date} non può essere aggiornato poiché era già 0 💩.")
    logger.info(f"Command /togli completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def conto_giorno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /conto_giorno command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /conta_giorno from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    
    if len(args) != 0 and len(args) != 1 and len(args) != 2:
        await update.message.reply_text("Formato non valido. Usa: /conta_giorno @username DD-MM-YYYY")
        return
    
    if len(args) == 0:
        username = update.message.from_user.username
        date = datetime.now(pytz.timezone('Europe/Rome')).strftime(DISPLAY_FORMAT)
        parsed_date = datetime.strptime(date, DISPLAY_FORMAT)
        selected_date = parsed_date.strftime(STORING_FORMAT)
    
    if len(args) == 1:
        if args[0].startswith('@'):
            username = args[0][1:]
            date = datetime.now(pytz.timezone('Europe/Rome')).strftime(DISPLAY_FORMAT)
            parsed_date = datetime.strptime(date, DISPLAY_FORMAT)
            selected_date = parsed_date.strftime(STORING_FORMAT)
        else:
            try:
                username = update.message.from_user.username
                date = args[0]
                parsed_date = datetime.strptime(date, DISPLAY_FORMAT)
                selected_date = parsed_date.strftime(STORING_FORMAT)
                today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
                if selected_date > today:
                    raise ValueError("La data selezionata è nel futuro.")
            except ValueError as e:
                await update.message.reply_text(f"Errore: {str(e)}")
                return
    
    if len(args) == 2:
        if not args[0].startswith('@'):
            await update.message.reply_text("Formato non valido. Usa: /conta_giorno @username DD-MM-YYYY")
            return
        try:
            username = args[0][1:]
            date = args[1]
            parsed_date = datetime.strptime(date, DISPLAY_FORMAT)
            selected_date = parsed_date.strftime(STORING_FORMAT)
            today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
            if selected_date > today:
                raise ValueError("La data selezionata è nel futuro.")
        except ValueError as e:
            await update.message.reply_text(f"Errore: {str(e)}")
            return

    count = get_count(username, selected_date, update.message.chat_id)
    
    if count != 0:
        await update.message.reply_text(f"@{username} il giorno {date if args else 'oggi'} hai fatto 💩 {count} {'volte' if count > 1 else 'volta'}.")
    else:
        await update.message.reply_text(f"@{username} {'il giorno ' + date if args else 'oggi'} non hai fatto .")
    logger.info(f"Command /conta_giorno completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

async def costipazione_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /costipazione command."""
    username: str = update.message.from_user.username
    logger.info(f"Command received: /costipazione from @{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")
    args = context.args
    if args:
        username = args[0][1:]
    else:
        username = update.message.from_user.username

    constipation_days = get_constipation_days(username, update.message.chat_id)
    
    if constipation_days is not None:
        if constipation_days == 0:
            await update.message.reply_text(f"@{username} oggi hai fatto 💩.")
        else:
            await update.message.reply_text(f"@{username} non fai 💩 da {constipation_days} {'giorni' if constipation_days > 1 else 'giorno'}.")
    else:
        await update.message.reply_text(f"@{username} non ci sono dati sulla costipazione.")
    logger.info(f"Command /costipazione completed in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}")

# Messages handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for processing messages."""
    if update.message:
        if update.message.text:
            text: str = update.message.text.lower().strip()
            username: str = update.message.from_user.username
            response: str = ""

            if not text: # Check for empty message
                logger.info(f"@{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}: Messaggio vuoto.")
                return # Exit the function, no further processing needed

            if BOT_USERNAME in text:
                response = "Cosa vuoi dirmi?"
            elif "💩" in text or "🚽" in text:
                today = datetime.now(pytz.timezone("Europe/Rome")).strftime(STORING_FORMAT)
                chat_id = update.message.chat_id

                count = get_count(username, today, chat_id) + 1
                update_count(username, today, count, chat_id)

                response = f"Complimenti @{username}, oggi hai fatto 💩 {count} " + ("volte!" if count > 1 else "volta!")
            elif re.search(r'\brun\b', text):
                response = f"@{username} cazzo scrivi *Run*, funziono solo con i comandi specifici e non quelli che ti inventi tu."

            if response:
                await update.message.reply_text(response, parse_mode='Markdown')

            # Log for debugging
            logger.info(f"@{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}: {text} | Risposta: {response}")
        elif update.message.sticker:
            username: str = update.message.from_user.username
            emoji = update.message.sticker.emoji # Get the emoji from sticker
            if emoji == "💩" or emoji == "🚽":
                today = datetime.now(pytz.timezone("Europe/Rome")).strftime(STORING_FORMAT)
                chat_id = update.message.chat_id

                count = get_count(username, today, chat_id) + 1
                update_count(username, today, count, chat_id)

                response = f"Complimenti @{username}, oggi hai fatto 💩 {count} " + ("volte!" if count > 1 else "volta!")
                await update.message.reply_text(response, parse_mode='Markdown')
                logger.info(f"@{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}: Sticker  | Risposta: {response}")
            else:
                logger.info(f"@{username} in {'PVT - ' if update._effective_message.chat.type == 'private' else 'GROUP - '}{update._effective_message.chat.effective_name}: Sticker {emoji} | Emoji non gestita.")
        else:
            logger.info(f"Update type not managed")
    else:
        logger.info(f"Update type not managed")

# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for logging errors."""
    if update:
        logger.error(f'Update "{update.update_id}" caused error "{context.error}"')
    else:
        logger.error(f'Error: "{context.error}"')

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
                application.run_polling(allowed_updates = Update.MESSAGE)
                break

            except KeyboardInterrupt:
                logger.info("Bot stopped by user.")
                break

            except Exception as e:
                logger.error(f"Error in polling: {e}")