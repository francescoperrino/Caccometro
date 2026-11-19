"""The Telegram application: logging, requests with retries, error handler and handler registration."""
import asyncio
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

import httpx
from telegram import Update
from telegram.error import NetworkError
from telegram.ext import Application, CommandHandler, ExtBot, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

from caccometro.commands import (start_command, leaderboard_month_command, leaderboard_year_command,
                                 stats_month_command, stats_year_command, records_command, add_poop_command,
                                 remove_poop_command, day_count_command, last_poop_command, link_history_command,
                                 trophies_command, language_command)
from caccometro.config import BOT_TOKEN, PROJECT_DIR, ROME_TZ, RUN_MODE
from caccometro.menus import MENU
from caccometro.messages import handle_message, handle_migration

# Enable logging
log_filename = os.environ.get('LOG_FILE', str(PROJECT_DIR / 'caccometro.log'))  # the tests point it elsewhere
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


def keep_app_log_out_of_the_root_logger(run_mode):
    """In webhook mode the bot's own records go straight to the file and stop at the 'caccometro' logger.

    The hosting puts a handler of its own on the root logger, after this module is imported (it shows every record,
    message only, in the web server error log). Records of the libraries still reach it: that is where their
    crashes belong. Polling mode (local development) keeps the console handler of log_handlers().
    """
    if run_mode != 'POLLING':
        app_logger = logging.getLogger('caccometro')
        app_logger.addHandler(file_handler)
        app_logger.propagate = False


# Log times in Italian time, like every date the bot shows (the server clock runs in UTC)
logging.Formatter.converter = staticmethod(lambda seconds: datetime.fromtimestamp(seconds, ROME_TZ).timetuple())
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO,
                    handlers=log_handlers(RUN_MODE))
keep_app_log_out_of_the_root_logger(RUN_MODE)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


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
        """The bot user, asked to Telegram only when it is not cached yet."""
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
    RETRY_DELAYS = (1, 2, 4, 8, 16)  # seconds between the 6 attempts: proxy 503 bursts can last more than 15 s

    async def do_request(self, *args, **kwargs):
        """Send the request, retrying with RETRY_DELAYS when the connection or the proxy fails."""
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

# Handlers by English name; names and menu descriptions are in menus.MENU
HANDLERS = {
    'start': start_command,
    'leaderboard_month': leaderboard_month_command,
    'leaderboard_year': leaderboard_year_command,
    'stats_month': stats_month_command,
    'stats_year': stats_year_command,
    'records': records_command,
    'trophies': trophies_command,
    'add_poop': add_poop_command,
    'remove_poop': remove_poop_command,
    'day_count': day_count_command,
    'last_poop': last_poop_command,
    'link_history': link_history_command,
    'language': language_command,
}
# English name, Italian name, handler: both names work in every chat
COMMANDS = [(english, italian, HANDLERS[english]) for english, italian, _, _ in MENU]
for english, italian, handler in COMMANDS:
    application.add_handler(CommandHandler([english, italian], handler))

# Messages (the migration handler comes first: only the first matching handler of a group runs)
application.add_handler(MessageHandler(filters.StatusUpdate.MIGRATE, handle_migration))
application.add_handler(MessageHandler(filters.ALL, handle_message))

# Errors
application.add_error_handler(error)


def main():
    """Run the bot in polling mode (local development); in webhook mode the web server imports `app` (see wsgi.py)."""
    if RUN_MODE == 'POLLING':
        logger.info("Starting bot in POLLING mode...")
        # run_polling retries network errors by itself and stops on Ctrl+C: no restart loop needed
        # (a loop restarted it on a closed event loop and failed again at once, forever)
        application.run_polling(allowed_updates=[Update.MESSAGE])
