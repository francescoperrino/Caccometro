"""Every "today" computation must use Europe/Rome, not the server timezone (UTC)."""
from datetime import datetime

import database
import utils


def test_now_rome_is_naive_and_in_rome_time():
    now = database.now_rome()
    assert now.tzinfo is None


def test_constipation_days_uses_rome_today(seed, chat_id, monkeypatch):
    seed({"mario": {"2024-03-10": 1}})
    monkeypatch.setattr(database, "now_rome", lambda: datetime(2024, 3, 13, 0, 30))
    assert database.get_constipation_days("mario", chat_id) == 3


def test_statistics_current_month_uses_rome_today(seed, chat_id, monkeypatch):
    # "Today" in Rome is March 10, 2024: the current month has 10 valid days, not 31
    seed({"mario": {"2024-03-02": 5}})
    monkeypatch.setattr(database, "now_rome", lambda: datetime(2024, 3, 10, 0, 30))
    (stat,) = database.get_statistics(chat_id, "month", "03-2024")
    assert stat["mean"] == 0.5  # 5 / 10


def test_statistics_current_year_uses_rome_today(seed, chat_id, monkeypatch):
    seed({"mario": {"2024-01-02": 4}})
    monkeypatch.setattr(database, "now_rome", lambda: datetime(2024, 1, 10, 0, 30))
    (stat,) = database.get_statistics(chat_id, "year", "2024")
    assert stat["mean"] == 0.4  # 4 / 10


def test_record_current_month_excluded_using_rome_today(monkeypatch):
    monkeypatch.setattr(utils, "now_rome", lambda: datetime(2024, 4, 1, 0, 30))
    rows = [("2024-03-10", 2), ("2024-04-01", 1)]
    result = utils.analyze_user_record(rows)
    # April is the current month (in Rome): only March remains
    assert result["max_monthly_count"] == 2
    assert result["max_months"] == "03-2024"
