"""Webhook: the Flask app the web server runs; Telegram posts every update to /webhook."""
import hmac
import logging
from collections import deque

from flask import Flask, request, Response, send_file
from telegram import Update
from telegram.error import BadRequest, Forbidden

from caccometro import __version__, database, i18n, miniapp
from caccometro.bot import application, outcome_of, update_log
from caccometro.commands import MAX_YEAR, MIN_YEAR
from caccometro.config import BOT_TOKEN, PROJECT_DIR, WEBHOOK_SECRET, now_rome

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Telegram sends an update again when the webhook fails or answers late: remember the last ones
# so that a 💩 is never counted twice. Kept in memory: enough, as a resend comes within minutes.
SEEN_UPDATE_IDS = deque(maxlen=500)

@app.route('/webhook', methods=['POST'])
async def webhook():
    """This function receives the update from Telegram and passes it to the library."""
    # Only Telegram knows the secret: without it anybody could send fake updates (compared as bytes: str raises on non-ASCII)
    received_secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    if not WEBHOOK_SECRET or not hmac.compare_digest(received_secret.encode(), WEBHOOK_SECRET.encode()):
        logger.warning("Webhook call without the right secret token: refused.")
        return Response('forbidden', status=403)
    logger.info("Webhook received...")
    # The line of the update covers the whole request: also the getMe of initialize() after a start, and its retries
    with update_log() as info:
        try:
            # 1. Read the update first: one already processed needs no start of the application at all
            update = Update.de_json(request.get_json(force=True), application.bot)
            if update.update_id in SEEN_UPDATE_IDS:
                logger.warning(f'Update "{update.update_id}" already processed: ignored.')
                return Response('ok', status=200)
            info['update'] = update

            # 2. Start the application and process the update; remembered only once started, so that an update
            # refused with a 500 because the start failed (getMe) is processed when Telegram sends it again
            await application.initialize()
            SEEN_UPDATE_IDS.append(update.update_id)
            await application.process_update(update)

            # Respond to Telegram that everything is ok
            return Response('ok', status=200)

        except Exception as e:
            info['outcome'] = outcome_of(e)
            logger.exception(f"Error in webhook: {e}")
            return Response('error', status=500)

        finally:
            # 3. Terminate the application
            # This "turns off" the bot and cleans up resources,
            # both in case of success (try) and in case of error (except).
            await application.shutdown()

MINI_APP_PAGE = PROJECT_DIR / 'assets' / 'webapp' / 'index.html'


@app.route('/app')
def mini_app():
    """The Mini App page (#79): static, it asks /api for the data with the initData Telegram gives it."""
    return send_file(MINI_APP_PAGE)


def mini_app_user():
    """The user who opened the Mini App, from the 'Authorization: tma <initData>' header; None if not signed."""
    return miniapp.user_of(request.headers.get('Authorization', '').removeprefix('tma '), BOT_TOKEN)


async def member_chat():
    """The chat of ?chat= when the signed user is one of its members: (chat_id, None), or (None, the error Response)."""
    user = mini_app_user()
    if user is None:
        return None, Response('unauthorized', status=401)
    try:
        chat_id = int(request.args.get('chat', ''))
    except ValueError:
        return None, Response('bad request', status=400)
    if chat_id not in miniapp.known_chats():
        return None, Response('not found', status=404)
    try:
        async with application:
            member = await miniapp.is_member(application.bot, chat_id, user['id'])
    except (BadRequest, Forbidden):
        member = False  # the bot is no longer in the group
    if not member:
        logger.info("Mini App: chat refused to a non-member")
        return None, Response('forbidden', status=403)
    return chat_id, None


@app.route('/api/chat')
async def api_chat():
    """Data of one chat, only for its members (left or kicked users get 403)."""
    chat_id, error = await member_chat()
    if error:
        return error
    logger.info("Mini App: chat opened")
    rows_by_user, users = database.get_all_user_rows(chat_id)
    timed = database.get_timed_conquests(chat_id)
    today = now_rome().date()
    return {'chat': chat_id, 'today': today.isoformat(), 'language': database.get_language(chat_id) or i18n.DEFAULT_LANGUAGE,
            'conquests': miniapp.conquest_data(timed, users),
            'records': miniapp.records_data(rows_by_user, today, timed)}


@app.route('/api/period')
async def api_period():
    """Leaderboard and statistics of ?year= (and ?month=) in one chat, only for its members."""
    chat_id, error = await member_chat()
    if error:
        return error
    try:
        year = int(request.args.get('year', ''))
        month = int(request.args['month']) if 'month' in request.args else None
    except ValueError:
        return Response('bad request', status=400)
    if not MIN_YEAR <= year <= MAX_YEAR or month is not None and not 1 <= month <= 12:
        return Response('bad request', status=400)
    time_period, period = ('year', str(year)) if month is None else ('month', f'{month:02d}-{year}')
    return miniapp.period_data(chat_id, time_period, period, now_rome().date())


@app.route('/')
def index():
    """Welcome page, useful for testing if the web app works; the deploy reads the version here."""
    return f'Ciao! Sono il Caccometro Bot, versione {__version__}. Il mio webhook è pronto.'
