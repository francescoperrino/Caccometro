"""Configuration: environment variables, date formats and the Rome time zone."""
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv

load_dotenv()
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # also given to set_webhook: Telegram sends it back
RUN_MODE = os.environ.get('RUN_MODE', 'POLLING').upper()

STORING_FORMAT = "%Y-%m-%d"  # Format used for storing dates in the database
DISPLAY_FORMAT = "%d-%m-%Y"  # Format used for displaying dates in messages
ROME_TZ = pytz.timezone('Europe/Rome')


def now_rome():
    """Current date/time in Rome, without tzinfo (comparable with the naive datetimes used in the code).

    The server runs in UTC: datetime.now() would return the wrong day
    between 22:00/23:00 and midnight in Italy.
    """
    return datetime.now(ROME_TZ).replace(tzinfo=None)
