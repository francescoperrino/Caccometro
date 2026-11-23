"""Webhook: the Flask app the web server runs; Telegram posts every update to /webhook."""
import hmac
import logging
from collections import deque

from flask import Flask, request, Response
from telegram import Update

from caccometro import __version__
from caccometro.bot import application, outcome_of, update_log
from caccometro.config import WEBHOOK_SECRET

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

@app.route('/')
def index():
    """Welcome page, useful for testing if the web app works; the deploy reads the version here."""
    return f'Ciao! Sono il Caccometro Bot, versione {__version__}. Il mio webhook è pronto.'
