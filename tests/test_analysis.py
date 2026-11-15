"""analysis.analyze_user: records and current status, with hand-computed expectations."""
import random
from datetime import date, timedelta

import pytest

from caccometro.analysis import Period, analyze_user

# Jan 2024: 1,2,1 on days 1-3, then day 7 | Feb: day 10 (x3) | Mar: day 1
ROWS = [
    ("2024-01-01", 1), ("2024-01-02", 2), ("2024-01-03", 1),
    ("2024-01-07", 1),
    ("2024-02-10", 3),
    ("2024-03-01", 1),
]
APRIL = date(2024, 4, 15)


def iso(day):
    return day.isoformat()


# ---------------------------------------------------------------- records

def test_daily_record():
    daily = analyze_user(ROWS, APRIL).daily
    assert daily.value == 3
    assert daily.when == [date(2024, 2, 10)]


def test_daily_record_keeps_every_tied_day():
    daily = analyze_user([("2024-01-01", 2), ("2024-01-05", 2), ("2024-01-06", 1)], APRIL).daily
    assert daily.value == 2
    assert daily.when == [date(2024, 1, 1), date(2024, 1, 5)]


def test_best_and_worst_month():
    records = analyze_user(ROWS, APRIL)
    assert records.best_month.value == 5 and records.best_month.when == [(2024, 1)]
    # worst: the first month (Jan) is not judged; Feb = 3, Mar = 1
    assert records.worst_month.value == 1 and records.worst_month.when == [(2024, 3)]


def test_the_current_month_is_not_a_completed_month():
    records = analyze_user(ROWS, date(2024, 3, 20))     # March is still running
    assert records.best_month.when == [(2024, 1)]
    assert records.worst_month.value == 3 and records.worst_month.when == [(2024, 2)]


def test_worst_month_counts_months_without_any_poop_between_first_and_last():
    rows = [("2024-01-10", 4), ("2024-03-05", 2)]                   # nothing at all in February
    worst = analyze_user(rows, date(2024, 6, 1)).worst_month
    assert worst.value == 0 and worst.when == [(2024, 2)]


def test_worst_month_does_not_count_the_months_after_the_last_data():
    rows = [("2024-01-10", 4), ("2024-02-05", 2)]                   # then silence for a year
    worst = analyze_user(rows, date(2025, 3, 1)).worst_month
    assert worst.value == 2 and worst.when == [(2024, 2)]           # not a long list of zeros


def test_worst_month_needs_two_months_of_data():
    assert analyze_user([("2024-01-10", 4)], date(2024, 6, 1)).worst_month is None
    assert analyze_user([("2024-01-10", 4), ("2024-02-10", 1)], date(2024, 2, 20)).worst_month is None


def test_monthly_records_do_not_exist_before_the_first_completed_month():
    records = analyze_user([("2024-04-10", 1), ("2024-04-12", 2)], APRIL)
    assert records.best_month is None and records.worst_month is None


def test_monthly_ties_keep_every_month():
    rows = [("2024-01-10", 2), ("2024-02-10", 2), ("2024-03-10", 1)]
    assert analyze_user(rows, APRIL).best_month.when == [(2024, 1), (2024, 2)]


def test_longest_streak_and_most_in_a_streak():
    records = analyze_user(ROWS, APRIL)
    assert records.streak_days.value == 3
    assert records.streak_days.when == [Period(date(2024, 1, 1), date(2024, 1, 3))]
    assert records.streak_count.value == 4
    assert records.streak_count.when == [Period(date(2024, 1, 1), date(2024, 1, 3))]


def test_streak_with_the_most_poop_can_differ_from_the_longest_one():
    rows = [("2024-01-01", 1), ("2024-01-02", 1), ("2024-01-03", 1), ("2024-02-10", 5), ("2024-02-11", 5)]
    records = analyze_user(rows, APRIL)
    assert records.streak_days.value == 3 and records.streak_days.when[0].start == date(2024, 1, 1)
    assert records.streak_count.value == 10 and records.streak_count.when == [Period(date(2024, 2, 10), date(2024, 2, 11))]


def test_streak_ties_keep_every_period():
    rows = [("2024-01-01", 1), ("2024-01-02", 1), ("2024-01-10", 1), ("2024-01-11", 1), ("2024-01-20", 1)]
    assert analyze_user(rows, APRIL).streak_days.when == [
        Period(date(2024, 1, 1), date(2024, 1, 2)), Period(date(2024, 1, 10), date(2024, 1, 11))]


def test_longest_pause():
    gap = analyze_user(ROWS, APRIL).gap_days
    assert gap.value == 33
    assert gap.when == [Period(date(2024, 1, 8), date(2024, 2, 9))]


def test_no_pause_when_there_are_no_days_in_between():
    assert analyze_user([("2024-01-01", 1), ("2024-01-02", 1)], APRIL).gap_days is None
    assert analyze_user([("2024-01-01", 1)], APRIL).gap_days is None


def test_days_with_a_zero_count_are_ignored():
    with_zero = analyze_user(ROWS + [("2024-01-04", 0), ("2024-01-05", 0)], APRIL)
    assert with_zero.streak_days.value == 3
    assert with_zero.gap_days.value == 33


# ---------------------------------------------------------------- current status

def test_status_with_nothing_going_on():
    status = analyze_user(ROWS, APRIL).status
    assert (status.today_count, status.month_count) == (0, 0)
    assert (status.streak_days, status.streak_count, status.streak_active_today) == (0, 0, False)
    assert status.gap_days == 45                                   # since 1 March


def test_status_with_a_streak_that_includes_today():
    rows = ROWS + [("2024-04-13", 1), ("2024-04-14", 2), ("2024-04-15", 1)]
    status = analyze_user(rows, APRIL).status
    assert status.today_count == 1 and status.month_count == 4
    assert (status.streak_days, status.streak_count, status.streak_active_today) == (3, 4, True)
    assert status.gap_days == 0


def test_a_streak_ending_yesterday_is_still_alive():
    rows = ROWS + [("2024-04-12", 1), ("2024-04-13", 1), ("2024-04-14", 3)]
    status = analyze_user(rows, APRIL).status
    assert (status.streak_days, status.streak_count, status.streak_active_today) == (3, 5, False)
    assert status.today_count == 0 and status.gap_days == 1


def test_a_streak_that_ended_the_day_before_yesterday_is_over():
    rows = ROWS + [("2024-04-12", 1), ("2024-04-13", 1)]
    status = analyze_user(rows, APRIL).status
    assert status.streak_days == 0 and status.streak_count == 0 and status.gap_days == 2


def test_only_the_current_run_counts_for_the_status():
    rows = [("2024-04-01", 5), ("2024-04-02", 5), ("2024-04-14", 1), ("2024-04-15", 2)]
    status = analyze_user(rows, APRIL).status
    assert (status.streak_days, status.streak_count) == (2, 3)
    assert status.month_count == 13


def test_month_count_counts_only_the_current_month():
    rows = [("2024-03-31", 9), ("2024-04-01", 1), ("2024-04-15", 1)]
    assert analyze_user(rows, APRIL).status.month_count == 2


def test_status_across_a_year_boundary():
    rows = [("2023-12-30", 1), ("2023-12-31", 1), ("2024-01-01", 1)]
    status = analyze_user(rows, date(2024, 1, 1)).status
    assert (status.streak_days, status.streak_count, status.month_count) == (3, 3, 1)
    records = analyze_user(rows, date(2024, 2, 5))
    assert records.best_month.when == [(2023, 12)]


# ---------------------------------------------------------------- invariants on random data

def test_invariants_on_random_data():
    rng = random.Random(5)
    for _ in range(300):
        start = date(2023, 1, 1) + timedelta(days=rng.randint(0, 300))
        today = start + timedelta(days=rng.randint(0, 400))
        rows = [(iso(start + timedelta(days=i)), rng.randint(1, 4))
                for i in range((today - start).days + 1) if rng.random() < rng.choice([0.2, 0.6, 0.95])]
        if not rows:
            continue
        counts = dict(rows)
        records = analyze_user(rows, today)
        status = records.status
        assert records.daily.value == max(counts.values())
        assert records.streak_days.value >= status.streak_days
        assert records.streak_count.value >= status.streak_count
        assert status.streak_days >= 1 or status.streak_count == 0
        assert status.today_count == counts.get(iso(today), 0)
        assert status.gap_days == (today - max(date.fromisoformat(d) for d in counts)).days
        assert all(p.start <= p.end for p in records.streak_days.when)
        if records.gap_days:
            assert all(p.start <= p.end for p in records.gap_days.when)
        if records.worst_month and records.best_month:
            assert records.worst_month.value <= records.best_month.value or len(counts) < 3


def test_months_are_in_chronological_order_even_if_the_rows_are_not():
    rows = [("2024-03-10", 2), ("2024-01-10", 2), ("2024-02-10", 2)]
    assert analyze_user(rows, date(2024, 6, 1)).best_month.when == [(2024, 1), (2024, 2), (2024, 3)]
