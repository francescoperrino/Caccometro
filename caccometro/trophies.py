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
    """Who made the most 💩 in a month or a year (ties: all of them) and how many."""
    total: int
    user_ids: list


class UserTrophies(NamedTuple):
    """The trophies of one user, in chronological order."""
    streaks: list   # [(Period, days)]: runs of at least STREAK_STEP days
    months: list    # [(year, month)]: months won
    years: list     # [year]: years won
    conqueror: tuple = ()   # [(year, quarter)]: seasons with the most conquests
    king: tuple = ()        # [(year, quarter)]: seasons ended as king of the hill

    @property
    def streak_trophies(self):
        """One trophy for every STREAK_STEP days of each run: a run of 47 days is worth 3."""
        return sum(days // STREAK_STEP for _, days in self.streaks)


def streak_runs(rows):
    """[(Period, days)] of the runs worth at least one trophy. rows: [(date 'YYYY-MM-DD', count)]."""
    counts = parse_counts(rows)
    return [(Period(run.start, run.end), run.days) for run in consecutive_runs(sorted(counts), counts)
            if run.days >= STREAK_STEP]


def new_streak_trophy(rows, today: date) -> Optional[int]:
    """Days of the run ending today if today makes them a multiple of STREAK_STEP; None otherwise."""
    counts = parse_counts(rows)
    if today not in counts:
        return None
    last = consecutive_runs(sorted(day for day in counts if day <= today), counts)[-1]
    return last.days if last.days % STREAK_STEP == 0 else None


def _winners(users_rows, period_of):
    """{period: Winners} of every period with 💩; period_of maps a date to its period."""
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
    """{(year, month): Winners} of the completed months. users_rows: {user_id: [(date, count)]}."""
    current = (today.year, today.month)
    return {month: winners for month, winners in _winners(users_rows, lambda d: (d.year, d.month)).items()
            if month < current}


def yearly_winners(users_rows, today: date):
    """{year: Winners} of the completed years."""
    return {year: winners for year, winners in _winners(users_rows, lambda d: d.year).items() if year < today.year}


class SeasonResult(NamedTuple):
    """Titles of a season (a calendar quarter in Italian time) of the conquest game."""
    conquests: int      # how many tiles the top conqueror(s) took during the season, stolen ones included
    conquerors: list    # user IDs with that many conquests (a tie gives the title to all of them)
    king: int           # user ID holding the most tiles at the end of the season (on a tie the sitting king keeps it)


def season_of(day: date):
    """(year, quarter 1-4) of a day."""
    return day.year, (day.month - 1) // 3 + 1


def season_results(history):
    """{season: SeasonResult} of every season with a conquest. history: [(user_id, ts, cell)] in the order handled.

    The king of a season comes from replaying the history up to its last conquest; the last season is "so far".
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
    """{user_id: UserTrophies} of the users with at least one trophy. history: conquests [(user_id, ts, cell)]."""
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
        trophies = UserTrophies(streak_runs(users_rows.get(user_id, [])), months.get(user_id, []),
                                years.get(user_id, []), conqueror.get(user_id, []), king.get(user_id, []))
        if any(trophies):
            result[user_id] = trophies
    return result
