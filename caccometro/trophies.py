"""Trophies: one every STREAK_STEP consecutive days with 💩, the 💩 of the month and of the year, the seasons of the conquest game.

Pure functions, like analysis.py: the trophies are computed from the stored counts, nothing is saved.
"""
from datetime import date, datetime
from typing import NamedTuple, Optional

from caccometro.analysis import Period, consecutive_runs, parse_counts
from caccometro.config import ROME_TZ
from caccometro.conquest import holdings

STREAK_STEP = 15   # a streak trophy every 15 consecutive days: 15, 30, 45, ...


class Winners(NamedTuple):
    """Who made the most 💩 in a month or a year (ties: all of them) and how many.

    Attributes:
        total (int): the 💩 of the winner or winners.
        user_ids (list): the user IDs with that total, sorted.
    """
    total: int
    user_ids: list


class UserTrophies(NamedTuple):
    """The trophies of one user, in chronological order.

    Attributes:
        streaks (list): [(Period, days)], runs of at least STREAK_STEP days.
        months (list): [(year, month)], months won.
        years (list): [year], years won.
        conqueror (tuple): [(year, quarter)], seasons with the most conquests.
        king (tuple): [(year, quarter)], seasons ended as king of the hill.
    """
    streaks: list
    months: list
    years: list
    conqueror: tuple = ()
    king: tuple = ()

    @property
    def streak_trophies(self):
        """One trophy for every STREAK_STEP days of each run: a run of 47 days is worth 3."""
        return sum(days // STREAK_STEP for _, days in self.streaks)


def _streak_runs(rows):
    """The runs of days with 💩 that are worth at least one trophy.

    Args:
        rows (list): [(date 'YYYY-MM-DD', count)] of one user.

    Returns:
        list: [(Period, days)] of the runs of at least STREAK_STEP days.
    """
    counts = parse_counts(rows)
    return [(Period(run.start, run.end), run.days) for run in consecutive_runs(sorted(counts), counts)
            if run.days >= STREAK_STEP]


def new_streak_trophy(rows, today: date) -> Optional[int]:
    """The length of the run that earns a trophy today, if any.

    Args:
        rows (list): [(date 'YYYY-MM-DD', count)] of one user.
        today: the current date.

    Returns:
        int: days of the run ending today if today makes them a multiple of STREAK_STEP; None otherwise.
    """
    counts = parse_counts(rows)
    if today not in counts:
        return None
    last = consecutive_runs(sorted(day for day in counts if day <= today), counts)[-1]
    return last.days if last.days % STREAK_STEP == 0 else None


def _winners(users_rows, period_of):
    """Who made the most 💩 in every period with 💩.

    Args:
        users_rows (dict): {user_id: [(date, count)]}.
        period_of (callable): maps a date to its period (a month, a year).

    Returns:
        dict: {period: Winners}.
    """
    totals = {}
    for user_id, rows in users_rows.items():
        for day, count in parse_counts(rows).items():
            per_user = totals.setdefault(period_of(day), {})
            per_user[user_id] = per_user.get(user_id, 0) + count
    result = {}
    for period, per_user in totals.items():
        top = max(per_user.values())
        result[period] = Winners(top, sorted(user_id for user_id, total in per_user.items() if total == top))
    return result


def monthly_winners(users_rows, today: date):
    """Who won every completed month.

    Args:
        users_rows (dict): {user_id: [(date, count)]}.
        today: the current date; the month it falls in is not completed.

    Returns:
        dict: {(year, month): Winners}.
    """
    current = (today.year, today.month)
    return {month: winners for month, winners in _winners(users_rows, lambda d: (d.year, d.month)).items()
            if month < current}


def yearly_winners(users_rows, today: date):
    """Who won every completed year.

    Args:
        users_rows (dict): {user_id: [(date, count)]}.
        today: the current date; the year it falls in is not completed.

    Returns:
        dict: {year: Winners}.
    """
    return {year: winners for year, winners in _winners(users_rows, lambda d: d.year).items() if year < today.year}


class SeasonResult(NamedTuple):
    """Titles of a season (a calendar quarter in Italian time) of the conquest game.

    Attributes:
        conquests (int): how many tiles the top conqueror or conquerors took during the season, stolen ones included.
        conquerors (list): user IDs with that many conquests (a tie gives the title to all of them).
        king (int): user ID holding the most tiles at the end of the season (on a tie the sitting king keeps it).
    """
    conquests: int
    conquerors: list
    king: int


def season_of(day: date):
    """The season of a day.

    Args:
        day: the day.

    Returns:
        (year, quarter): the quarter is 1 to 4.
    """
    return day.year, (day.month - 1) // 3 + 1


def season_results(history):
    """The titles of every season with a conquest.

    The king of a season comes from replaying the history up to its last conquest; the last season is "so far".

    Args:
        history (list): [(user_id, ts, cell)] in the order the conquests were handled.

    Returns:
        dict: {season: SeasonResult}.
    """
    # owners: tile -> current owner; per_season: season -> {user ID: conquests}; last: season -> index of its last conquest
    owners, per_season, last = {}, {}, {}
    for i, (user_id, ts, cell) in enumerate(history):
        season = season_of(datetime.fromtimestamp(ts, ROME_TZ).date())
        last[season] = i
        if owners.get(cell) != user_id:   # taking a tile you already own is not a conquest
            owners[cell] = user_id
            counts = per_season.setdefault(season, {})
            counts[user_id] = counts.get(user_id, 0) + 1
    result = {}
    for season, counts in per_season.items():
        top = max(counts.values())
        king = holdings([(user_id, cell) for user_id, _, cell in history[:last[season] + 1]])[1]
        result[season] = SeasonResult(top, sorted(user_id for user_id, n in counts.items() if n == top), king)
    return result


def trophies_by_user(users_rows, today: date, history=()):
    """The trophies of every user who has at least one.

    Args:
        users_rows (dict): {user_id: [(date, count)]}.
        today: the current date; unfinished months, years and seasons give no trophy.
        history (list): conquests [(user_id, ts, cell)].

    Returns:
        dict: {user_id: UserTrophies}.
    """
    months, years = {}, {}
    for month, winners in sorted(monthly_winners(users_rows, today).items()):
        for user_id in winners.user_ids:
            months.setdefault(user_id, []).append(month)
    for year, winners in sorted(yearly_winners(users_rows, today).items()):
        for user_id in winners.user_ids:
            years.setdefault(user_id, []).append(year)
    conqueror, king = {}, {}
    for season, season_result in sorted(season_results(history).items()):
        if season < season_of(today):
            for user_id in season_result.conquerors:
                conqueror.setdefault(user_id, []).append(season)
            king.setdefault(season_result.king, []).append(season)
    result = {}
    for user_id in set(users_rows) | set(conqueror) | set(king):
        trophies = UserTrophies(_streak_runs(users_rows.get(user_id, [])), months.get(user_id, []),
                                years.get(user_id, []), conqueror.get(user_id, []), king.get(user_id, []))
        if any(trophies):
            result[user_id] = trophies
    return result
