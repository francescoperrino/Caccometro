"""Configuration: environment variables, date formats and the Rome time zone."""
import calendar
import os
from datetime import datetime
from pathlib import Path

import pytz
from dotenv import load_dotenv

load_dotenv()
PROJECT_DIR = Path(__file__).resolve().parent.parent  # database and log live here, whatever the working directory
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # also given to set_webhook: Telegram sends it back
RUN_MODE = os.environ.get('RUN_MODE', 'POLLING').upper()

STORING_FORMAT = "%Y-%m-%d"  # Format used for storing dates in the database
DISPLAY_FORMAT = "%d-%m-%Y"  # Format used for displaying dates in messages
ROME_TZ = pytz.timezone('Europe/Rome')
# Italian month names, written out: calendar.month_name depends on the process locale
MONTH_NAMES = ['', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
               'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']


def now_rome():
    """Current date/time in Rome, without tzinfo (comparable with the naive datetimes used in the code).

    The server runs in UTC: datetime.now() would return the wrong day
    between 22:00/23:00 and midnight in Italy.
    """
    return datetime.now(ROME_TZ).replace(tzinfo=None)


def period_bounds(time_period, date):
    """Start and end date (storing format) of a month ('MM-YYYY') or year ('YYYY')."""
    if time_period == 'month':
        # Parse the input date for monthly rank (format: month-year)
        date_parts = date.split('-')
        month_str = date_parts[0].zfill(2)  # Add leading zero, if necessary
        year_str = date_parts[1]
        start_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y').strftime(STORING_FORMAT)
        # Get the end of the month
        end_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y')\
                        .replace(day=calendar.monthrange(int(year_str), int(month_str))[1])\
                        .strftime(STORING_FORMAT)
    elif time_period == 'year':
        # Parse the input date for yearly rank (format: year)
        start_period = datetime.strptime(f'01-01-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
        end_period = datetime.strptime(f'31-12-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
    else:
        raise ValueError("Invalid time_period. It should be 'month' or 'year'.")
    return start_period, end_period
