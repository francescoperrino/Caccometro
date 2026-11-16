"""Webhook: the Flask app the web server runs; Telegram posts every update to /webhook."""
import hmac
import logging
from collections import deque

from flask import Flask, request, Response
from telegram import Update

from caccometro import __version__
from caccometro.bot import application
from caccometro.config import WEBHOOK_SECRET

logger = logging.getLogger(__name__)

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
    """Welcome page, useful for testing if the web app works; the deploy reads the version here."""
    return f'Ciao! Sono il Caccometro Bot, versione {__version__}. Il mio webhook è pronto.'
