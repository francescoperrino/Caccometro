"""Records and current status of the users' 💩 counts.

Pure functions: they receive plain data (rows of (date, count)) and the current date, and never touch
the database or Telegram, so they can be tested with hand-computed examples.
"""
from datetime import date, datetime, timedelta
from typing import NamedTuple, Optional, Tuple

import numpy as np

from caccometro.database import User

STORING_FORMAT = "%Y-%m-%d"

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
    daily: Record                    # most 💩 in one day
    best_month: Optional[Record]     # most 💩 in a completed month; None before the first completed month
    worst_month: Optional[Record]    # fewest 💩 in a completed month (see _worst_month); None if not available
    streak_days: Record              # longest run of consecutive days with 💩
    streak_count: Record             # most 💩 in one run of consecutive days
    gap_days: Optional[Record]       # longest completed pause between two days with 💩; None if there is none
    status: Status


class _Run(NamedTuple):
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
