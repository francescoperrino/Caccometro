"""Webhook: the Flask app the web server runs; Telegram posts every update to /webhook."""
import hmac
import logging
from collections import deque

from flask import Flask, request, Response, send_file
from telegram import Update
from telegram.error import BadRequest, Forbidden

from caccometro import __version__, database, i18n, miniapp
from caccometro.bot import application, outcome_of, update_log
from caccometro.config import BOT_TOKEN, PROJECT_DIR, WEBHOOK_SECRET

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


def language_of(chat_id, known):
    """Language of a chat with a database (`known`); the default one otherwise, without creating its database."""
    return (database.get_language(chat_id) if chat_id in known else None) or i18n.DEFAULT_LANGUAGE


@app.route('/api/chats')
async def api_chats():
    """Group picker: the chats whose database knows the user, with the group titles from Telegram."""
    user = mini_app_user()
    if user is None:
        return Response('unauthorized', status=401)
    known = miniapp.known_chats()
    chats = []
    async with application:
        for chat_id in miniapp.chats_of(user['id']):
            if chat_id == user['id']:
                chats.append({'id': chat_id, 'title': None})  # the private chat: the page names it
                continue
            try:
                chats.append({'id': chat_id, 'title': (await application.bot.get_chat(chat_id)).title})
            except (BadRequest, Forbidden):
                pass  # the bot left the group, or the group is gone
    logger.info(f"Mini App: {len(chats)} chats listed")
    return {'language': language_of(user['id'], known), 'chats': chats}


@app.route('/api/chat')
async def api_chat():
    """Data of one chat, only for its members (left or kicked users get 403)."""
    user = mini_app_user()
    if user is None:
        return Response('unauthorized', status=401)
    try:
        chat_id = int(request.args.get('chat', ''))
    except ValueError:
        return Response('bad request', status=400)
    known = miniapp.known_chats()
    if chat_id not in known:
        return Response('not found', status=404)
    try:
        async with application:
            member = await miniapp.is_member(application.bot, chat_id, user['id'])
    except (BadRequest, Forbidden):
        member = False  # the bot is no longer in the group
    if not member:
        logger.info("Mini App: chat refused to a non-member")
        return Response('forbidden', status=403)
    logger.info("Mini App: chat opened")
    return {'chat': chat_id, 'language': language_of(chat_id, known)}


@app.route('/')
def index():
    """Welcome page, useful for testing if the web app works; the deploy reads the version here."""
    return f'Ciao! Sono il Caccometro Bot, versione {__version__}. Il mio webhook è pronto.'
