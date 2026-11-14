"""Records and current status of the users' 💩 counts.

Pure functions: they receive plain data (rows of (date, count)) and the current date, and never touch
the database or Telegram, so they can be tested with hand-computed examples.
"""
from datetime import date, datetime, timedelta
from typing import NamedTuple, Optional, Tuple

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

