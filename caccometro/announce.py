"""Midnight announcement of the 💩 of the month (on January 1st also of the year, on a quarter's first day the season) in every chat.

Run by a daily scheduled task on the hosting, from the folder that holds `db/`:
    python3.10 -m caccometro.announce
The task starts at 22:00 UTC, which is 23:00 (winter) or 00:00 (summer) in Italy: the script waits
until midnight when it is close, then posts only if the new day is the first of a month.

Options: --date YYYY-MM-DD to announce as if that day had just begun (no waiting),
--dry-run to print the messages instead of sending them.
"""
import argparse
import asyncio
import logging
import os
import re
import time
from datetime import date, datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from caccometro import database, i18n, miniapp
from caccometro.bot import application
from caccometro.chat import escape_md
from caccometro.config import BOT_USERNAME, now_rome
from caccometro.formatting import format_new_period
from caccometro.i18n import tr
from caccometro.trophies import monthly_winners, season_of, season_results, yearly_winners

logger = logging.getLogger(__name__)

MAX_WAIT = timedelta(hours=2)   # wait for midnight only when it is this close
DB_NAME = re.compile(r'^(-?\d+)_bot_data\.db$')


def chat_ids():
    """IDs of the chats that have a database."""
    if not os.path.isdir(database.DB_FOLDER):
        return []
    return sorted(int(match.group(1)) for name in os.listdir(database.DB_FOLDER) if (match := DB_NAME.match(name)))


def announcement(chat_id, today: date):
    """Message for the chat on `today` (the first day of a month), in its language; None when there is nobody to celebrate."""
    i18n.use(database.get_language(chat_id))
    rows_by_user, users = database.get_all_user_rows(chat_id)
    ended = today - timedelta(days=1)
    month = monthly_winners(rows_by_user, today).get((ended.year, ended.month))
    year = yearly_winners(rows_by_user, today).get(ended.year) if today.month == 1 else None
    names = {user_id: escape_md(user.mention) for user_id, user in users.items()}
    season = None
    if today.month % 3 == 1:   # first day of a quarter: the season that just ended
        key = season_of(ended)
        result = season_results(database.get_timed_conquests(chat_id)).get(key)
        season = (key, result) if result else None
    return format_new_period(today, month, year, names, season)



def recap_button(chat_id, today):
    """Buttons under the announcement of a new month that open the Mini App on the recap of the month just ended, and on
    the 1st of January on the recap of the year too (#195)."""
    buttons = [InlineKeyboardButton(tr("✨ Il tuo mese"), url=miniapp.direct_link(BOT_USERNAME, chat_id, 'recap'))]
    if today.month == 1:
        buttons.insert(0, InlineKeyboardButton(tr("✨ Il tuo anno"), url=miniapp.direct_link(BOT_USERNAME, chat_id, 'year')))
    return InlineKeyboardMarkup([buttons])


async def announce(today: date, dry_run=False):
    """Send the announcement to every chat; a chat that fails (e.g. the bot was removed) does not stop the others."""
    messages = []
    for chat_id in chat_ids():
        try:
            text = announcement(chat_id, today)
        except Exception:
            logger.exception(f"Announcement for chat {chat_id} failed")
            continue
        if text is not None:
            messages.append((chat_id, text, recap_button(chat_id, today)))
    if dry_run:
        for chat_id, text, _ in messages:
            print(f"--- {chat_id}\n{text}\n")
        return
    sent = 0
    async with application.bot:
        for chat_id, text, button in messages:
            try:
                await application.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=button)
                sent += 1
            except Exception:
                logger.exception(f"Announcement for chat {chat_id} failed")
    logger.info(f"Announcement of {today}: sent to {sent} of {len(messages)} chat(s)")


def wait_for_midnight(now: datetime):
    """Sleep until the next midnight in Italy when it is less than MAX_WAIT away; return that midnight, or None.

    The caller announces for the returned day: waking up a moment before midnight must not change it.
    """
    midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    if midnight - now > MAX_WAIT:
        return None
    time.sleep((midnight - now).total_seconds())
    return midnight


def main(argv=None):
    """Entry point of the scheduled task."""
    parser = argparse.ArgumentParser(description="Announce the 💩 of the month and of the year.")
    parser.add_argument('--date', type=date.fromisoformat, help="announce as if this day had just begun")
    parser.add_argument('--dry-run', action='store_true', help="print the messages instead of sending them")
    args = parser.parse_args(argv)

    today = args.date
    if today is None:
        midnight = wait_for_midnight(now_rome())
        today = midnight.date() if midnight else now_rome().date()
    if today.day != 1:
        logger.info(f"Announcement: {today} is not the first day of a month, nothing to do")
        return
    asyncio.run(announce(today, args.dry_run))


if __name__ == '__main__':
    main()
