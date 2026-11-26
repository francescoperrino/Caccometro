"""Arguments of the commands: periods, dates, the person a command refers to."""
import re
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from caccometro.chat import register_user
from caccometro.config import DISPLAY_FORMAT, MONTH_NAMES, now_rome
from caccometro.database import find_user_by_username
from caccometro.i18n import MONTHS, tr


def parse_username_arg(arg):
    """'@mario' -> 'mario'; None if it does not start with @ or is empty."""
    if not arg.startswith('@') or len(arg) < 2:
        return None
    return arg[1:]


MIN_YEAR, MAX_YEAR = 1970, 2100  # the years accepted in the arguments of the commands


# '-', '/' and '.' are the same separator; the year has 2 digits (20YY) or 4; leading zeros are optional
MONTH_ARG = re.compile(r'([0-9]{1,2})[-/.]([0-9]{2}|[0-9]{4})')
MONTH_NAME_ARG = re.compile(r'([a-z]+)(?: ([0-9]{2}|[0-9]{4}))?')  # 'marzo 2026', 'marzo 26' or 'marzo' (this year)
DATE_ARG = re.compile(r'([0-9]{1,2})[-/.]([0-9]{1,2})(?:[-/.]([0-9]{2}|[0-9]{4}))?')  # without the year: this year
# Words accepted in every chat, whatever its language
MONTH_NUMBERS = {name.lower(): number for names in (MONTH_NAMES, *MONTHS.values())
                 for number, name in enumerate(names) if number}
DAYS_AGO = {'oggi': 0, 'today': 0, 'ieri': 1, 'yesterday': 1}


def _year_of(text):
    """'26' -> 2026, '2026' -> 2026."""
    return 2000 + int(text) if len(text) == 2 else int(text)


def parse_month_arg(arg):
    """'3-2024', '03/24', '03.2024', 'marzo 2024' or 'march 2024' -> '03-2024'; None if it is not a valid month (years 1970-2100)."""
    arg = arg.strip().lower()
    match = MONTH_ARG.fullmatch(arg)
    if match is not None:
        month, year = int(match.group(1)), _year_of(match.group(2))
    else:
        match = MONTH_NAME_ARG.fullmatch(arg)
        if match is None or match.group(1) not in MONTH_NUMBERS:
            return None
        month = MONTH_NUMBERS[match.group(1)]
        year = _year_of(match.group(2)) if match.group(2) else now_rome().year
    return f'{month:02d}-{year}' if 1 <= month <= 12 and MIN_YEAR <= year <= MAX_YEAR else None


def parse_year_arg(arg):
    """'2024' or '24' -> '2024'; None if it is not a valid year (2 or 4 digits, 1970-2100)."""
    if re.fullmatch(r'([0-9]{2}|[0-9]{4})', arg) and MIN_YEAR <= _year_of(arg) <= MAX_YEAR:
        return str(_year_of(arg))
    return None


def parse_date_arg(arg):
    """'5/3/26', '05.03.2026', '5.3', 'oggi', 'yesterday'... -> ('05-03-2026', '2026-03-05').

    Raises ValueError, with the message for the user, if invalid, before 1970 or in the future.
    """
    today = now_rome().date()
    word, match = arg.lower(), DATE_ARG.fullmatch(arg)
    try:
        if word in DAYS_AGO:
            selected_date = today - timedelta(days=DAYS_AGO[word])
        else:
            year = _year_of(match.group(3)) if match.group(3) else today.year
            selected_date = datetime(year, int(match.group(2)), int(match.group(1))).date()
    except (AttributeError, ValueError):  # no match, or a day that does not exist
        raise ValueError(tr("Data non valida. Esempi: 05-03-2026, 5/3/26, 5.3 (anno corrente), oggi, ieri.")) from None
    if selected_date > today:
        raise ValueError(tr("La data selezionata è nel futuro."))
    if selected_date.year < MIN_YEAR:
        raise ValueError(tr("L'anno deve essere dal {year} in poi.").format(year=MIN_YEAR))
    # isoformat, not strftime: on Linux '%Y' does not pad the year with zeros
    return selected_date.strftime(DISPLAY_FORMAT), selected_date.isoformat()


def resolve_target(update: Update, args, sender, usage):
    """Work out whose data a command refers to.

    Order: an explicit '@username' as first argument (it must belong to a user the bot has already
    seen), then the author of the message being replied to, then the sender.
    Returns (target, remaining_args, error_message); target is None when there is an error.
    """
    chat_id = update.message.chat_id
    if args and args[0].startswith('@'):
        username = parse_username_arg(args[0])
        if username is None:
            return None, args, invalid_format(usage)
        target = find_user_by_username(chat_id, username)
        if target is None:
            return None, args, tr("🤔 Non conosco @{username}: deve scrivere almeno un messaggio nel gruppo "
                                  "(oppure rispondi a un suo messaggio).").format(username=username)
        return target, args[1:], None
    replied = replied_person(update)
    if replied is not None:
        return register_user(chat_id, replied), args, None
    return sender, args, None


def invalid_format(usage):
    """The reply to arguments that do not fit the command."""
    return tr("⚠️ Formato non valido. Usa: {usage}").format(usage=usage)


def replied_person(update: Update):
    """The Telegram user of the message being replied to, or None when the reply is not to a person.

    A bot is not a person. Inside a forum topic every message is a reply to the message that created
    the topic: that is not a reply to its author either.
    """
    replied = update.message.reply_to_message
    if replied is None or replied.forum_topic_created is not None or replied.from_user is None or replied.from_user.is_bot:
        return None
    return replied.from_user


def resolve_optional_target(update: Update, context: ContextTypes.DEFAULT_TYPE, sender, usage):
    """Target of /records and /trophies: io, @username or a reply. Returns (target, error); no target and no error means the group."""
    if len(context.args) == 1 and context.args[0].lower() in ("io", "me"):
        return sender, None
    if not context.args and replied_person(update) is None:
        return None, None
    target, args, error = resolve_target(update, context.args, sender, usage)
    if error is None and args:
        error = invalid_format(usage)
    return target, error
