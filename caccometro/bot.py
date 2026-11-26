"""The Telegram application: logging, requests with retries, error handler and handler registration."""
import asyncio
import logging
import os
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from logging.handlers import RotatingFileHandler

import httpx
from telegram import Update
from telegram.error import BadRequest, NetworkError
from telegram.ext import Application, CommandHandler, ExtBot, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

from caccometro.cmd_conquests import conquests_command
from caccometro.cmd_counts import add_poop_command, day_count_command, last_poop_command, remove_poop_command
from caccometro.cmd_leaderboards import (leaderboard_month_command, leaderboard_year_command, stats_month_command,
                                         stats_year_command)
from caccometro.cmd_records import records_command, trophies_command
from caccometro.cmd_settings import app_command, language_command, link_history_command, start_command
from caccometro.config import BOT_TOKEN, PROJECT_DIR, ROME_TZ, RUN_MODE
from caccometro.menus import MENU
from caccometro.messages import handle_message, handle_migration

log_filename = os.environ.get('LOG_FILE', str(PROJECT_DIR / 'caccometro.log'))  # the tests point it elsewhere
LOG_MAX_BYTES = 1_000_000  # 1 MB per file...
LOG_BACKUPS = 3            # ...and 3 older files: the logs never take more than about 4 MB
file_handler = RotatingFileHandler(log_filename, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUPS, encoding='utf-8')


def _log_handlers(run_mode):
    """The handlers of the bot log: the rotating file, and the console too only when running locally.

    In webhook mode the console is the web server error log: writing there too kept every line twice.
    Crashes before logging is set up (e.g. at import) still reach it.

    Args:
        run_mode (str): 'POLLING' (local) or another value (webhook).

    Returns:
        list: the logging handlers.
    """
    if run_mode == 'POLLING':
        return [file_handler, logging.StreamHandler()]
    return [file_handler]


def _keep_app_log_out_of_the_root_logger(run_mode):
    """In webhook mode send the bot's own records straight to the file and stop them at the 'caccometro' logger.

    The hosting puts a handler of its own on the root logger, after this module is imported (it shows every record,
    message only, in the web server error log). Records of the libraries still reach it: that is where their
    crashes belong. Polling mode (local development) keeps the console handler of _log_handlers().

    Args:
        run_mode (str): 'POLLING' (local) or another value (webhook).
    """
    if run_mode != 'POLLING':
        app_logger = logging.getLogger('caccometro')
        app_logger.addHandler(file_handler)
        app_logger.propagate = False


# Log times in Italian time, like every date the bot shows (the server clock runs in UTC)
logging.Formatter.converter = staticmethod(lambda seconds: datetime.fromtimestamp(seconds, ROME_TZ).timetuple())
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO,
                    handlers=_log_handlers(RUN_MODE))
_keep_app_log_out_of_the_root_logger(RUN_MODE)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Requests to Telegram and outcome of the update being processed, for its "done" line (see _LoggingApplication)
CURRENT_UPDATE = ContextVar('current_update', default=None)


def _update_kind(update):
    """What the update asked the bot, for the log.

    Args:
        update (Update): the incoming update.

    Returns:
        str: '/<English command name>', 'sticker', 'location', 'message' or 'other'.
    """
    message = getattr(update, 'message', None)
    if message is None:
        return 'other'
    if message.text and message.text.startswith('/'):
        name = message.text.split()[0][1:].split('@')[0].lower()
        english = next((english for english, italian, _ in COMMANDS if name in (english, italian)), None)
        if english:
            return f'/{english}'
    if message.sticker:
        return 'sticker'
    if message.location:
        return 'location'
    return 'message'


def _update_line(update, attempts, outcome, ms):
    """The line written when an update is done: no names, no text, only what the nightly summary needs.

    Args:
        update (Update): the update.
        attempts (int): the requests made to Telegram while handling it.
        outcome (str): 'ok', 'lost' or 'error'.
        ms (int): how long it took, in milliseconds.

    Returns:
        str: the line.
    """
    chat = getattr(update, 'effective_chat', None)
    chat_type = '-' if chat is None else 'private' if chat.type == 'private' else 'group'
    update_id = getattr(update, 'update_id', '-')
    return (f"Update {update_id} done: command={_update_kind(update)} chat={chat_type} ms={ms} "
            f"attempts={attempts} outcome={outcome}")


def outcome_of(error):
    """How an exception ended an update.

    Args:
        error (Exception): what was raised.

    Returns:
        str: 'lost' when the network gave up (the reply did not arrive), 'error' for any other exception.
    """
    return 'lost' if isinstance(error, NetworkError) and not isinstance(error, BadRequest) else 'error'


@contextmanager
def update_log():
    """Time what runs inside and count its requests to Telegram; then log the line of info['update'], when set.

    The webhook wraps the whole request with it, so the getMe of the first update after a start is counted too.

    Yields:
        dict: info with 'attempts', 'outcome' and 'update'; the caller sets 'update' to get the line.
    """
    info = {'attempts': 0, 'outcome': 'ok', 'update': None}
    token = CURRENT_UPDATE.set(info)
    start = time.monotonic()
    try:
        yield info
    except Exception as e:
        info['outcome'] = outcome_of(e)
        raise
    finally:
        CURRENT_UPDATE.reset(token)
        if info['update'] is not None:
            ms = round((time.monotonic() - start) * 1000)
            logger.info(_update_line(info['update'], info['attempts'], info['outcome'], ms))


class _LoggingApplication(Application):
    """Application that writes one line per update when its processing ends (see _update_line)."""

    async def process_update(self, update):
        """Process the update as usual, timing it and counting its requests to Telegram (polling mode).

        Args:
            update (Update): the incoming update.

        Returns:
            The result of the usual processing.
        """
        if CURRENT_UPDATE.get() is not None:  # the webhook already times the whole request
            return await super().process_update(update)
        with update_log() as info:
            info['update'] = update
            await super().process_update(update)


async def _error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log an error of a handler; the update is marked as lost (network gave up) or failed.

    Args:
        update (Update): the update being handled, or None.
        context (ContextTypes.DEFAULT_TYPE): holds `context.error`, what was raised.
    """
    info = CURRENT_UPDATE.get()
    if info is not None:
        info['outcome'] = outcome_of(context.error)
    if update:
        logger.error(f'Update "{getattr(update, "update_id", "-")}" caused error "{context.error}" in {_update_kind(update)}',
                     exc_info=context.error)
    else:
        logger.error(f'Error: "{context.error}"', exc_info=context.error)

class _CachedMeBot(ExtBot):
    """ExtBot that asks Telegram 'who am I?' (getMe) only once per process.

    The webhook initializes and shuts down the application for every update, and Bot.initialize()
    calls getMe each time: one extra outbound request per message, and one more chance to hit a
    proxy error. The answer never changes, so it is kept after the first success (a failed call is
    not cached and is simply tried again).
    """

    async def get_me(self, *args, **kwargs):
        """The bot user, asked to Telegram only when it is not cached yet.

        Args:
            *args: passed to ExtBot.get_me.
            **kwargs: passed to ExtBot.get_me.

        Returns:
            telegram.User: the bot user.
        """
        if self._bot_user is not None:
            return self._bot_user
        return await super().get_me(*args, **kwargs)


class _RetryingRequest(HTTPXRequest):
    """HTTPXRequest that tries a request again when the connection to Telegram fails.

    Outgoing requests sometimes fail at once with a proxy error (503) and work a moment later.
    Only errors raised before the request reached Telegram are retried: after a timeout or a
    dropped connection the message may already have been delivered, and a retry would send it twice.
    """
    RETRYABLE = (httpx.ProxyError, httpx.ConnectError)
    RETRY_DELAYS = (1, 2, 4, 8, 16)  # seconds between the 6 attempts: proxy 503 bursts can last more than 15 s

    async def do_request(self, *args, **kwargs):
        """Send the request, retrying with RETRY_DELAYS when the connection or the proxy fails.

        Args:
            *args: passed to HTTPXRequest.do_request.
            **kwargs: passed to HTTPXRequest.do_request.

        Returns:
            The response of HTTPXRequest.do_request.
        """
        info = CURRENT_UPDATE.get()
        for delay in self.RETRY_DELAYS:
            if info is not None:
                info['attempts'] += 1
            try:
                return await super().do_request(*args, **kwargs)
            except NetworkError as e:
                if not isinstance(e.__cause__, self.RETRYABLE):
                    raise
                logger.warning(f"Telegram request failed ({e}), new attempt in {delay} s")
                await asyncio.sleep(delay)
        if info is not None:
            info['attempts'] += 1
        return await super().do_request(*args, **kwargs)


# Create the Application instance (same connection pools as Application.builder().token(...) would use)
application = Application.builder().application_class(_LoggingApplication).bot(_CachedMeBot(
    BOT_TOKEN,
    request=_RetryingRequest(connection_pool_size=256),
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
    'conquests': conquests_command,
    'app': app_command,
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

application.add_error_handler(_error)


def main():
    """Run the bot in polling mode (local development).

    In webhook mode the web server imports `app` (see wsgi.py).
    """
    if RUN_MODE == 'POLLING':
        logger.info("Starting bot in POLLING mode...")
        # run_polling retries network errors by itself and stops on Ctrl+C: no restart loop needed
        # (a loop restarted it on a closed event loop and failed again at once, forever)
        application.run_polling(allowed_updates=[Update.MESSAGE])
