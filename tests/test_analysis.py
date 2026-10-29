"""Characterization tests for utils.analyze_user_record."""
import utils

# Jan 2024: 1,2,1 consecutive (1-3), gap, day 7 | Feb: day 10 (x3) | Mar: day 1
ROWS = [
    ("2024-01-01", 1), ("2024-01-02", 2), ("2024-01-03", 1),
    ("2024-01-07", 1),
    ("2024-02-10", 3),
    ("2024-03-01", 1),
]


def test_daily_max():
    r = utils.analyze_user_record(ROWS)
    assert r["max_daily_count"] == 3
    assert r["max_days"] == "10-02-2024"


def test_monthly_max_min():
    r = utils.analyze_user_record(ROWS)
    assert r["max_monthly_count"] == 5 and r["max_months"] == "01-2024"
    assert r["min_monthly_count"] == 1 and r["min_months"] == "03-2024"


def test_longest_streak_and_streak_count():
    r = utils.analyze_user_record(ROWS)
    assert r["max_streak_days"] == 3
    assert r["max_streak_period"] == "01-01-2024 - 03-01-2024"
    assert r["max_streak_count"] == 4
    assert r["max_streak_count_period"] == "01-01-2024 - 03-01-2024"


def test_longest_gap():
    r = utils.analyze_user_record(ROWS)
    # 08-01 .. 09-02 = 33 days without 💩
    assert r["max_gap_days"] == 33
    assert r["max_gap_period"] == "08-01-2024 - 09-02-2024"
