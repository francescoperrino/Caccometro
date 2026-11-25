"""Records and current status of the users' 💩 counts.

Pure functions: they receive plain data (rows of (date, count)) and the current date, and never touch
the database or Telegram, so they can be tested with hand-computed examples.
"""
from datetime import date, datetime, timedelta
from typing import NamedTuple, Optional, Tuple

import numpy as np

from caccometro.config import STORING_FORMAT
from caccometro.database import User

Month = Tuple[int, int]  # (year, month)


class Period(NamedTuple):
    """A range of days, both ends included."""
    start: date
    end: date


class Record(NamedTuple):
    """The best value of a metric and everything that reached it (ties are all kept).

    'when' holds dates, months ((year, month)) or Periods, depending on the metric.
    """
    value: int
    when: list


class Status(NamedTuple):
    """Where the user stands right now, metric by metric."""
    today_count: int
    month_count: int             # 💩 so far in the current month
    streak_days: int             # consecutive days with 💩 up to today (or up to yesterday)
    streak_count: int            # 💩 recorded in that run of days
    streak_active_today: bool    # False when the run ended yesterday (today has no 💩 yet)
    gap_days: Optional[int]      # days since the last 💩 (0 = today); None if there is no data
    streak_period: Optional[Period]  # first and last day of the run in progress; None if there is none


class UserRecords(NamedTuple):
    """Personal records of one user, plus the current status they are compared with."""

    daily: Record                    # most 💩 in one day
    best_month: Optional[Record]     # most 💩 in a completed month; None before the first completed month
    worst_month: Optional[Record]    # fewest 💩 in a completed month (see _worst_month); None if not available
    streak_days: Record              # longest run of consecutive days with 💩
    streak_count: Record             # most 💩 in one run of consecutive days
    gap_days: Optional[Record]       # longest completed pause between two days with 💩; None if there is none
    status: Status


class _Run(NamedTuple):
    """A run of consecutive days with 💩: first and last day, length and total 💩."""

    start: date
    end: date
    days: int
    total: int


def _parse(rows):
    """[(date string, count)] -> {date: count}, ignoring days without 💩."""
    return {datetime.strptime(day, STORING_FORMAT).date(): count for day, count in rows if count > 0}


def _runs(days_sorted, counts):
    """Runs of consecutive days with 💩."""
    runs = []
    for day in days_sorted:
        if runs and (day - runs[-1].end).days == 1:
            previous = runs[-1]
            runs[-1] = _Run(previous.start, day, previous.days + 1, previous.total + counts[day])
        else:
            runs.append(_Run(day, day, 1, counts[day]))
    return runs


def _best(items, key):
    """Maximum of key(item) and all the items that reach it; None if there are no items."""
    if not items:
        return None
    top = max(key(item) for item in items)
    return top, [item for item in items if key(item) == top]


def _next_month(month: Month) -> Month:
    """The (year, month) after `month`."""
    year, number = month
    return (year + 1, 1) if number == 12 else (year, number + 1)


def _worst_month(monthly, first_month: Month, last_month: Month, current_month: Month):
    """Fewest 💩 in a month, among the months that can be judged fairly.

    A month counts if it is completed (before the current one), it is not the first month with data
    (the user may have started halfway through it) and it is not after the last month with data
    (the user may have left). Months in between with no 💩 at all count as 0.
    """
    months = []
    month = _next_month(first_month)
    while month <= last_month and month < current_month:
        months.append(month)
        month = _next_month(month)
    if not months:
        return None
    lowest = min(monthly.get(m, 0) for m in months)
    return Record(lowest, [m for m in months if monthly.get(m, 0) == lowest])


def analyze_user(rows, today: date) -> UserRecords:
    """Records and current status of one user.

    rows: [(date 'YYYY-MM-DD', count)], at least one row with a positive count.
    today: the current date (passed in so that results are reproducible).
    """
    counts = _parse(rows)
    days = sorted(counts)
    runs = _runs(days, counts)

    top_count, top_days = _best(days, lambda d: counts[d])
    daily = Record(top_count, top_days)

    top_days_len, longest = _best(runs, lambda r: r.days)
    streak_days = Record(top_days_len, [Period(r.start, r.end) for r in longest])
    top_total, richest = _best(runs, lambda r: r.total)
    streak_count = Record(top_total, [Period(r.start, r.end) for r in richest])

    gaps = [Period(a + timedelta(days=1), b - timedelta(days=1)) for a, b in zip(days, days[1:]) if (b - a).days > 1]
    longest_gap = _best(gaps, lambda g: (g.end - g.start).days + 1)
    gap_days = Record(longest_gap[0], longest_gap[1]) if longest_gap else None

    monthly = {}
    for day, count in counts.items():
        monthly[(day.year, day.month)] = monthly.get((day.year, day.month), 0) + count
    current_month = (today.year, today.month)
    completed = sorted(m for m in monthly if m < current_month)
    best = _best(completed, lambda m: monthly[m])
    best_month = Record(best[0], best[1]) if best else None
    worst_month = _worst_month(monthly, min(monthly), max(monthly), current_month)

    last = days[-1]
    last_run = runs[-1]
    run_is_current = last in (today, today - timedelta(days=1))
    status = Status(
        today_count=counts.get(today, 0),
        month_count=monthly.get(current_month, 0),
        streak_days=last_run.days if run_is_current else 0,
        streak_count=last_run.total if run_is_current else 0,
        streak_active_today=last == today,
        gap_days=max((today - last).days, 0),
        streak_period=Period(last_run.start, last_run.end) if run_is_current else None,
    )
    return UserRecords(daily, best_month, worst_month, streak_days, streak_count, gap_days, status)


# ---------------------------------------------------------------- the whole group

ACTIVE_DAYS = 90   # a user whose last 💩 is older than this is not considered when looking at "right now"


class Holder(NamedTuple):
    """Someone who holds (or shares) a group record."""
    key: object      # whatever identifies the user (the user ID)
    when: list       # dates, months or Periods where the value was reached (see UserRecords)


class Leaders(NamedTuple):
    """The best value of a metric in the group and everyone who reached it."""
    value: int
    holders: list    # [Holder]


class GroupBoard(NamedTuple):
    """Records of the whole group: who holds each record of all times and who leads right now."""

    # records of all times
    daily: Optional[Leaders]          # most 💩 in one day
    best_month: Optional[Leaders]     # most 💩 in a completed month
    worst_month: Optional[Leaders]    # fewest 💩 in a completed month
    streak_days: Optional[Leaders]    # longest run of consecutive days
    streak_count: Optional[Leaders]   # most 💩 in one run
    gap_days: Optional[Leaders]       # longest completed pause
    # right now (active users only)
    today: Optional[Leaders]          # most 💩 today
    active_streak: Optional[Leaders]  # longest run in progress (value in days)
    active_gap: Optional[Leaders]     # longest pause in progress (value in days)


def _leaders(candidates, lowest=False):
    """candidates: [(key, value, when)] -> Leaders of the highest (or lowest) value; None if empty."""
    if not candidates:
        return None
    pick = min if lowest else max
    top = pick(value for _, value, _ in candidates)
    return Leaders(top, [Holder(key, when) for key, value, when in candidates if value == top])


def analyze_group(users_rows, today: date) -> GroupBoard:
    """Who holds each record of the group, and who leads right now.

    users_rows: {user key: [(date 'YYYY-MM-DD', count)]}; users without any 💩 are ignored.
    """
    records = {key: analyze_user(rows, today) for key, rows in users_rows.items()
               if any(count > 0 for _, count in rows)}

    def from_records(pick, lowest=False):
        """Leaders of the record that `pick` takes from each user's records."""
        return _leaders([(key, record.value, record.when) for key, record in
                         ((key, pick(r)) for key, r in records.items()) if record is not None], lowest)

    active = {key: r.status for key, r in records.items() if r.status.gap_days <= ACTIVE_DAYS}
    return GroupBoard(
        daily=from_records(lambda r: r.daily),
        best_month=from_records(lambda r: r.best_month),
        worst_month=from_records(lambda r: r.worst_month, lowest=True),
        streak_days=from_records(lambda r: r.streak_days),
        streak_count=from_records(lambda r: r.streak_count),
        gap_days=from_records(lambda r: r.gap_days),
        today=_leaders([(key, s.today_count, []) for key, s in active.items() if s.today_count > 0]),
        active_streak=_leaders([(key, s.streak_days, [s.streak_period])
                                for key, s in active.items() if s.streak_days > 0]),
        active_gap=_leaders([(key, s.gap_days, []) for key, s in active.items() if s.gap_days > 0]),
    )


FORECAST_WINDOW_DAYS = 30


def forecast_totals(totals, recent_counts, today: date, end_period):
    """Expected 💩 of every user at the end of the period: the total so far plus, for each day left,
    the user's mean daily 💩 over the last FORECAST_WINDOW_DAYS days (today included).

    The window crosses the start of the period, so the forecast is steady from the first day of a month or year.
    totals: {user_id: 💩 so far}; recent_counts: {user_id: {'YYYY-MM-DD': count}} of the window;
    end_period: 'YYYY-MM-DD'.
    """
    days_left = (date.fromisoformat(end_period) - today).days
    # shortcut: a user who started counting less than FORECAST_WINDOW_DAYS days ago gets a too low rate;
    # divide by the days since their first count if new users complain.
    return {user_id: total + round(sum(recent_counts.get(user_id, {}).values()) / FORECAST_WINDOW_DAYS * days_left)
            for user_id, total in totals.items()}


def period_statistics(daily_counts, users, start_period, end_period, today: date):
    """Mean, median and variance of the daily 💩 of every user in a period, best mean first (ties: lower variance).

    daily_counts: {user_id: {'YYYY-MM-DD': count}}, days without 💩 absent (they count as 0);
    users: {user_id: User}; start_period/end_period: 'YYYY-MM-DD'.
    The current period counts only the days gone by, today included.
    """
    first_day = date.fromisoformat(start_period)
    last_day = date.fromisoformat(end_period)
    ongoing = first_day <= today <= last_day
    valid_days = ((today if ongoing else last_day) - first_day).days + 1

    statistics = []
    for user_id, per_day in daily_counts.items():
        counts = [per_day[day] for day in sorted(per_day)]
        if len(counts) < valid_days:
            counts += [0] * (valid_days - len(counts))
        elif len(counts) > valid_days:
            counts = counts[:valid_days]

        mean = round(sum(counts) / valid_days, 2)
        statistics.append({
            'user': users.get(user_id) or User(user_id, None, str(user_id)),
            'mean': mean,
            'median': np.median(counts),
            'variance': round(sum((x - mean) ** 2 for x in counts) / valid_days, 2),
        })
    return sorted(statistics, key=lambda s: (-s['mean'], s['variance']))


REGULARITY_MIN_DAYS, REGULARITY_MIN_POOPS = 14, 5   # below this the label would be noise
# The index of dispersion (variance / mean of the daily counts): 1 = as random as dice, lower = steadier.
# Thresholds from the real groups (November 2026 backups, 282 months of one person: quartiles 0.31 and 0.56), so
# about a quarter of the months read "very regular" and a fifth "up and down"; no published threshold exists.
REGULARITY_STEPS = ((0.3, 'molto regolare'), (0.6, 'abbastanza regolare'))


def regularity(counts):
    """'molto regolare', 'abbastanza regolare' or 'a sbalzi' from the daily counts (0 on days without), None with too little data."""
    if len(counts) < REGULARITY_MIN_DAYS or sum(counts) < REGULARITY_MIN_POOPS:
        return None
    mean = sum(counts) / len(counts)
    dispersion = sum((x - mean) ** 2 for x in counts) / (len(counts) - 1) / mean
    return next((label for limit, label in REGULARITY_STEPS if dispersion < limit), 'a sbalzi')


def period_regularity(daily, first_days, user_id, start, end, today):
    """regularity() of one person in a period ('YYYY-MM-DD' bounds), on whole days only:
    from their first 💩 (not before they joined) to yesterday."""
    first = max(date.fromisoformat(start), date.fromisoformat(first_days.get(user_id, start)))
    last = min(date.fromisoformat(end), today - timedelta(days=1))
    return regularity([daily.get(user_id, {}).get((first + timedelta(days=i)).isoformat(), 0)
                       for i in range((last - first).days + 1)])


RECORD_KEYS = ('daily', 'best_month', 'worst_month', 'streak_days', 'streak_count', 'gap_days')


def record_places(user_id, people):
    """{metric: (place, how many have it, shared)} of one person's records among those of everybody (people: {user_id: UserRecords}).

    Ties share the place; in 'worst_month' the lower is better, like the Mini App. Metrics held by one person only are left out.
    """
    places = {}
    for key in RECORD_KEYS:
        values = {u: getattr(r, key).value for u, r in people.items() if getattr(r, key) is not None}
        if user_id not in values or len(values) < 2:
            continue
        mine = values[user_id]
        place = 1 + sum((v < mine) if key == 'worst_month' else (v > mine) for v in values.values())
        places[key] = (place, len(values), sum(v == mine for v in values.values()) > 1)
    return places
