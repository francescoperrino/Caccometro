"""Mini App (#79): who opened it (signed initData), which chats they may see, and the direct link from the groups."""
import hashlib
import hmac
import json
import os
import time
from datetime import date, datetime, timedelta
from urllib.parse import parse_qsl

import h3
from telegram.constants import ChatMemberStatus

from caccometro import charts, database, maps
from caccometro.analysis import (FORECAST_WINDOW_DAYS, RECAP_DAYS, YEAR_RECAP_DAYS, analyze_group, analyze_user, forecast_totals, recap,
                                 period_regularity, period_statistics)
from caccometro.config import ROME_TZ, now_rome, period_bounds
from caccometro.conquest import holdings, mention_of
from caccometro.trophies import season_of, season_results, trophies_by_user

SHORT_NAME = 'app'          # short name given to /newapp on BotFather, the same on both bots
MAX_AGE_SECONDS = 24 * 3600  # older initData is refused: a copied link stops working after a day
MEMBER_SECONDS = 5 * 60      # a membership check is trusted this long, to spare calls through the proxy

_members = {}  # (user_id, chat_id) -> time of the last positive check


def direct_link(bot_username, chat_id, view=None):
    """Link that opens the Mini App already on a chat, and with `view` ('recap' or 'year', #195) on the recap of the month
    or of the year; plain URL buttons can carry it, in groups too (web_app buttons only work in private chats)."""
    return f"https://t.me/{bot_username}/{SHORT_NAME}?startapp={chat_id}" + (f'_{view}' if view else '')


def user_of(init_data, token, now=None):
    """The Telegram user (dict) who opened the Mini App, or None when initData is not signed by Telegram or too old.

    Check from the Telegram docs: HMAC-SHA256 of the sorted "key=value" lines, with HMAC("WebAppData", token) as key.
    """
    fields = dict(parse_qsl(init_data or '', keep_blank_values=True))
    received = fields.pop('hash', '')
    check = '\n'.join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()
    # compared as bytes: two str with non-ASCII characters make compare_digest raise
    if not hmac.compare_digest(hmac.new(secret, check.encode(), hashlib.sha256).hexdigest().encode(), received.encode()):
        return None
    try:
        fresh = (now or time.time()) - int(fields['auth_date']) < MAX_AGE_SECONDS
        user = json.loads(fields['user'])
    except (KeyError, ValueError):
        return None
    return user if fresh and isinstance(user.get('id'), int) else None


def known_chats():
    """IDs of every chat that has a database: the API never opens (and so never creates) the database of another one."""
    suffix = '_bot_data.db'
    names = os.listdir(database.DB_FOLDER) if os.path.isdir(database.DB_FOLDER) else []
    return [int(name[:-len(suffix)]) for name in names if name.endswith(suffix) and name[:-len(suffix)].lstrip('-').isdigit()]


async def is_member(bot, chat_id, user_id):
    """Whether the user is still in the chat; the private chat with the bot is always theirs."""
    if chat_id == user_id:
        return True
    checked = _members.get((user_id, chat_id))
    if checked and time.time() - checked < MEMBER_SECONDS:
        return True
    member = await bot.get_chat_member(chat_id, user_id)
    ok = member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED) and getattr(member, 'is_member', True)
    if ok:
        _members[(user_id, chat_id)] = time.time()
    return ok


LEVELS = range(7, 0, -1)  # h3 resolutions sent: the page picks one by zoom, 7 = the tiles of the game


def conquest_data(timed, users):
    """The conquest map of a chat for the page (#189). timed: [(user_id, ts, cell)] in order; users: {user_id: User}.

    One list of hexagons per resolution, like the maps of /conquests: each hexagon has its owner (who holds most
    tiles inside), how many tiles each member holds ('held') and ever conquered ('seen') inside, and its outline
    computed here; the saved locations never leave the server.
    """
    history = [(user_id, cell) for user_id, _, cell in timed]
    counts, king = holdings(history)
    tiles = maps.owners(history)
    levels = {}
    for res in LEVELS:
        owner_of = maps.grouped(tiles, res)
        held, seen = {}, {}  # parent hexagon -> {user_id: tiles inside held now / ever conquered}
        for user_id, cell in set(history):
            inside = seen.setdefault(h3.cell_to_parent(cell, res), {})
            inside[user_id] = inside.get(user_id, 0) + 1
        for cell, (user_id, _) in tiles.items():
            inside = held.setdefault(h3.cell_to_parent(cell, res), {})
            inside[user_id] = inside.get(user_id, 0) + 1
        levels[res] = [{'owner': owner, 'held': held[parent], 'seen': seen[parent],
                        'outline': [list(corner) for corner in h3.cell_to_boundary(parent)]}
                       for parent, owner in owner_of.items()]
    names = {user_id: mention_of(users, user_id) for user_id in {user_id for user_id, _ in history} | set(users)}
    season = season_of(now_rome().date())
    result = season_results(timed).get(season)
    return {'levels': levels, 'names': names, 'king': king, 'seasons': season_boards(timed),
            'ranking': [{'user': user_id, 'held': held} for user_id, held in
                        sorted(counts.items(), key=lambda item: (-item[1], item[0] != king))],
            'season': None if result is None else {'year': season[0], 'quarter': season[1], 'conquests': result.conquests,
                                                   'conquerors': result.conquerors, 'king': result.king}}


def plain(value):
    """Records and trophies ready for JSON: dates as 'YYYY-MM-DD', named tuples (Record, Period...) as objects."""
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, '_asdict'):
        return {key: plain(item) for key, item in value._asdict().items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def records_data(rows_by_user, today, timed):
    """Records of the group and of each person, and everyone's trophies (#190): what /records and /trophies show."""
    people = {user_id: analyze_user(rows, today) for user_id, rows in rows_by_user.items() if any(c > 0 for _, c in rows)}
    return {'group': plain(analyze_group(rows_by_user, today)),
            'people': {user_id: plain(records) for user_id, records in people.items()},
            'trophies': {user_id: {**plain(trophies), 'streak_trophies': trophies.streak_trophies}
                         for user_id, trophies in trophies_by_user(rows_by_user, today, timed).items()}}


def period_data(chat_id, time_period, period, today):
    """Leaderboard with the forecast and statistics of a month ('MM-YYYY') or year ('YYYY'), like the commands (#190).

    'daily' carries the counts of every day for the charts drawn by the page.
    """
    start, end = period_bounds(time_period, period)
    rank = database.get_rank(chat_id, time_period, period)
    daily = database.get_daily_counts_between(chat_id, start, end)
    forecast = {}
    if rank and start <= today.isoformat() <= end:  # ongoing period, as in leaderboard_command
        recent = database.get_daily_counts_between(
            chat_id, (today - timedelta(days=FORECAST_WINDOW_DAYS - 1)).isoformat(), today.isoformat())
        forecast = forecast_totals({user.user_id: total for user, total in rank}, recent, today, end)
    statistics = period_statistics(daily, database.get_users(chat_id), start, end, today)
    first_days = database.get_first_days(chat_id)
    return {'start': start, 'end': end, 'today': today.isoformat(), 'daily': daily,
            'leaderboard': [{'user': user.user_id, 'total': total, 'forecast': forecast.get(user.user_id)}
                            for user, total in rank],
            'statistics': [{'user': s['user'].user_id, 'mean': s['mean'], 'median': float(s['median']),
                            'variance': s['variance'],
                            'regularity': period_regularity(daily, first_days, s['user'].user_id, start, end, today)}
                           for s in statistics]}


def season_boards(timed):
    """Every season with a conquest, oldest first (#190): the conquests each member made in it, stolen tiles included
    (the rule of the conqueror title), and the tiles each one held at its end (now, for the current season), with its king."""
    conquered, last, owners = {}, {}, {}
    for i, (user_id, ts, cell) in enumerate(timed):
        season = season_of(datetime.fromtimestamp(ts, ROME_TZ).date())
        last[season] = i
        counts = conquered.setdefault(season, {})
        if owners.get(cell) != user_id:   # taking a tile you already own is not a conquest
            owners[cell] = user_id
            counts[user_id] = counts.get(user_id, 0) + 1
    boards = []
    for season in sorted(last):
        held, king = holdings([(user_id, cell) for user_id, _, cell in timed[:last[season] + 1]])
        boards.append({'year': season[0], 'quarter': season[1], 'conquests': conquered[season], 'held': held, 'king': king})
    return boards


def recap_data(chat_id, user_id, today, yearly=False):
    """The recap (#195) of one person: of the month just ended from the 1st to the RECAP_DAYS-th of a month, or with
    `yearly` of the year just ended from the 1st to the YEAR_RECAP_DAYS-th of January; None on other days or without 💩."""
    if yearly:
        if today.month != 1 or today.day > YEAR_RECAP_DAYS:
            return None
        year, month = today.year - 1, None
        start, end = date(year - 1, 1, 1), date(year, 12, 31)
    else:
        if today.day > RECAP_DAYS:
            return None
        end = today.replace(day=1) - timedelta(days=1)
        year, month = end.year, end.month
        start = (end.replace(day=1) - timedelta(days=1)).replace(day=1)
    daily = database.get_daily_counts_between(chat_id, start.isoformat(), end.isoformat())
    return recap(daily, user_id, year, month, database.get_first_days(chat_id))


def recaps(chat_id, user_id, today):
    """The recaps to show today, the year first: none, one, or in early January the year and December."""
    return [plain(r) for r in (recap_data(chat_id, user_id, today, yearly=True), recap_data(chat_id, user_id, today)) if r]


LINK_SECONDS = 15 * 60  # how long the link of a recap picture works (#217)


def _link_signature(payload, token):
    return hmac.new(hashlib.sha256(b'RecapLink' + token.encode()).digest(), payload.encode(), hashlib.sha256).hexdigest()


def recap_link(chat_id, user_id, yearly, token, now=None):
    """The name of a short-lived link to a recap picture (#217), for the download of Telegram, which sends no initData:
    "chat.user.yearly.expiry.signature", signed with a key drawn from the bot token, so nobody can forge one."""
    payload = f"{chat_id}.{user_id}.{int(yearly)}.{int(now or time.time()) + LINK_SECONDS}"
    return f"{payload}.{_link_signature(payload, token)}"


def recap_of_link(name, token, now=None):
    """(chat_id, user_id, yearly) of a link made by recap_link, or None when it is forged or expired."""
    payload, _, signature = name.rpartition('.')
    if not hmac.compare_digest(_link_signature(payload, token).encode(), signature.encode()):
        return None
    chat_id, user_id, yearly, expiry = (int(part) for part in payload.split('.'))
    return (chat_id, user_id, yearly == 1) if (now or time.time()) < expiry else None


def recap_image(chat_id, user_id, recap):
    """The recap as the PNG to share, with the names the chat knows."""
    users = database.get_users(chat_id)
    return charts.generate_recap_image(recap, mention_of(users, user_id))
