"""Trophies: one every STREAK_STEP consecutive days with 💩, the 💩 of the month and the 💩 of the year.

Pure functions, like analysis.py: the trophies are computed from the stored counts, nothing is saved.
"""
from datetime import date
from typing import NamedTuple, Optional

from caccometro.analysis import Period, _parse, _runs

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

    @property
    def streak_trophies(self):
        """One trophy for every STREAK_STEP days of each run: a run of 47 days is worth 3."""
        return sum(days // STREAK_STEP for _, days in self.streaks)


def streak_runs(rows):
    """[(Period, days)] of the runs worth at least one trophy. rows: [(date 'YYYY-MM-DD', count)]."""
    counts = _parse(rows)
    return [(Period(run.start, run.end), run.days) for run in _runs(sorted(counts), counts)
            if run.days >= STREAK_STEP]


def new_streak_trophy(rows, today: date) -> Optional[int]:
    """Days of the run ending today if today makes them a multiple of STREAK_STEP; None otherwise."""
    counts = _parse(rows)
    if today not in counts:
        return None
    last = _runs(sorted(day for day in counts if day <= today), counts)[-1]
    return last.days if last.days % STREAK_STEP == 0 else None


def _winners(users_rows, period_of):
    """{period: Winners} of every period with 💩; period_of maps a date to its period."""
    totals = {}
    for user_id, rows in users_rows.items():
        for day, count in _parse(rows).items():
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


def trophies_by_user(users_rows, today: date):
    """{user_id: UserTrophies} of the users with at least one trophy."""
    months, years = {}, {}
    for month, winners in sorted(monthly_winners(users_rows, today).items()):
        for user_id in winners.user_ids:
            months.setdefault(user_id, []).append(month)
    for year, winners in sorted(yearly_winners(users_rows, today).items()):
        for user_id in winners.user_ids:
            years.setdefault(user_id, []).append(year)
    result = {}
    for user_id, rows in users_rows.items():
        trophies = UserTrophies(streak_runs(rows), months.get(user_id, []), years.get(user_id, []))
        if trophies.streaks or trophies.months or trophies.years:
            result[user_id] = trophies
    return result
