"""Arguments of the commands: periods, dates, the person a command refers to."""
import re
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from caccometro.chat import register_user
from caccometro.config import DISPLAY_FORMAT, MONTH_NAMES, now_rome
from caccometro.database import find_user_by_username
from caccometro.i18n import MONTHS, tr


def _parse_username_arg(arg):
    """The username in an argument like '@mario'.

    Args:
        arg (str): the argument.

    Returns:
        str: the username without the @; None if the argument does not start with @ or is just '@'.
    """
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
    """A year of 2 or 4 digits as a number: '26' gives 2026, '2026' gives 2026.

    Args:
        text (str): the digits.

    Returns:
        int: the year.
    """
    return 2000 + int(text) if len(text) == 2 else int(text)


def _parse_month_arg(arg):
    """A month written in any accepted way.

    Accepted: '3-2024', '03/24', '03.2024', 'marzo 2024' or 'march 2024'; years 1970 to 2100.

    Args:
        arg (str): the argument.

    Returns:
        str: the month as '03-2024'; None if it is not a valid month.
    """
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


def _parse_year_arg(arg):
    """A year of 2 or 4 digits, between 1970 and 2100.

    Args:
        arg (str): the argument, like '2024' or '24'.

    Returns:
        str: the year as '2024'; None if it is not a valid year.
    """
    if re.fullmatch(r'([0-9]{2}|[0-9]{4})', arg) and MIN_YEAR <= _year_of(arg) <= MAX_YEAR:
        return str(_year_of(arg))
    return None


def _parse_date_arg(arg):
    """A date written in any accepted way: '5/3/26', '05.03.2026', '5.3', 'oggi', 'yesterday'...

    Args:
        arg (str): the argument.

    Returns:
        (display, storing): for instance ('05-03-2026', '2026-03-05').

    Raises:
        ValueError: the date is not valid, is before 1970 or is in the future; the message is for the user.
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


def _resolve_target(update: Update, args, sender, usage):
    """Work out whose data a command refers to.

    Order: an explicit '@username' as first argument (it must belong to a user the bot has already seen), then the
    author of the message being replied to, then the sender.

    Args:
        update (Update): the incoming message.
        args (list): the arguments of the command.
        sender (User): who wrote the command.
        usage (str): how the command is used, for the error message.

    Returns:
        (target, remaining_args, error_message): target is None when there is an error.
    """
    chat_id = update.message.chat_id
    if args and args[0].startswith('@'):
        username = _parse_username_arg(args[0])
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
    """The reply to arguments that do not fit the command.

    Args:
        usage (str): how the command is used.

    Returns:
        str: the message.
    """
    return tr("⚠️ Formato non valido. Usa: {usage}").format(usage=usage)


def replied_person(update: Update):
    """The Telegram user of the message being replied to.

    A bot is not a person. Inside a forum topic every message is a reply to the message that created
    the topic: that is not a reply to its author either.

    Args:
        update (Update): the incoming message.

    Returns:
        telegram.User: the author; None when the reply is not to a person.
    """
    replied = update.message.reply_to_message
    if replied is None or replied.forum_topic_created is not None or replied.from_user is None or replied.from_user.is_bot:
        return None
    return replied.from_user


def resolve_optional_target(update: Update, context: ContextTypes.DEFAULT_TYPE, sender, usage):
    """Target of /records and /trophies: io, @username or a reply.

    Args:
        update (Update): the incoming message.
        context (ContextTypes.DEFAULT_TYPE): holds `context.args`, the arguments of the command.
        sender (User): who wrote the command.
        usage (str): how the command is used, for the error message.

    Returns:
        (target, error): no target and no error means the group.
    """
    if len(context.args) == 1 and context.args[0].lower() in ("io", "me"):
        return sender, None
    if not context.args and replied_person(update) is None:
        return None, None
    target, args, error = _resolve_target(update, context.args, sender, usage)
    if error is None and args:
        error = invalid_format(usage)
    return target, error


async def target_from_args(update: Update, args, sender, usage, counts):
    """The person of a command and the arguments after it, whose number must be in `counts`.

    Tells the user what is wrong when it is not.

    Args:
        update (Update): the incoming message.
        args (list): the arguments of the command.
        sender (User): who wrote the command.
        usage (str): how the command is used, for the error message.
        counts (tuple): how many arguments may remain after the person.

    Returns:
        (target, remaining_args): None after telling the user what is wrong.
    """
    target, args, error = _resolve_target(update, args, sender, usage)
    if error is None and len(args) not in counts:
        error = invalid_format(usage)
    if error:
        await update.message.reply_text(error)
        return None
    return target, args


async def date_from_arg(update: Update, arg):
    """Read a date argument, or tell the user why it is not valid.

    Args:
        update (Update): the incoming message.
        arg (str): the argument.

    Returns:
        tuple: the result of _parse_date_arg; None after telling the user.
    """
    try:
        return _parse_date_arg(arg)
    except ValueError as e:
        await update.message.reply_text(tr("⚠️ Errore: {error}").format(error=e))
        return None


# The two kinds of period of the commands; their sentences are chosen with `month and ... or ...`
PERIODS = {
    'month': {'parse': _parse_month_arg, 'current': '%m-%Y'},
    'year': {'parse': _parse_year_arg, 'current': '%Y'},
}


async def period_from_args(update: Update, args, time_period):
    """The period asked for, the current one without arguments.

    Tells the user when the argument is not a valid period.

    Args:
        update (Update): the incoming message.
        args (list): the arguments of the command.
        time_period (str): 'month' or 'year'.

    Returns:
        str: 'MM-YYYY' or 'YYYY'; None when the argument is not valid.
    """
    period = PERIODS[time_period]
    if not args:
        return now_rome().strftime(period['current'])
    date = period['parse'](' '.join(args))  # joined: 'marzo 2026' arrives as two arguments
    if date is None:
        await update.message.reply_text(
            tr("⚠️ Formato data non valido. Usa MM-YYYY (anche 3/2026, 03.26 o marzo 2026).") if time_period == 'month'
            else tr("⚠️ Formato anno non valido. Usa YYYY (anche 26)."))
    return date
