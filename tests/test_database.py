"""Characterization tests for database.py: they pin the current behavior."""
from datetime import datetime, timedelta

import database


def test_update_and_get_count_roundtrip(seed, chat_id):
    seed({"mario": {"2024-03-10": 2}})
    assert database.get_count("mario", "2024-03-10", chat_id) == 2
    assert database.get_count("mario", "2024-03-11", chat_id) == 0
    assert database.get_count("luigi", "2024-03-10", chat_id) == 0


def test_update_count_zero_deletes_row(seed, chat_id):
    seed({"mario": {"2024-03-10": 2}})
    database.update_count("mario", "2024-03-10", 0, chat_id)
    assert database.get_record("mario", chat_id) == []


def test_get_count_accepts_day_month_and_display_format(seed, chat_id):
    seed({"mario": {"2024-03-10": 2, "2024-03-20": 1, "2024-04-01": 5}})
    assert database.get_count("mario", "2024-03", chat_id) == 3      # month
    assert database.get_count("mario", "10-03-2024", chat_id) == 2   # DD-MM-YYYY
    assert database.get_count("mario", "non-una-data", chat_id) == 0


def test_get_rank_month_and_year_ordering(seed, chat_id):
    seed({
        "mario": {"2024-03-10": 2, "2024-03-20": 1, "2024-04-01": 5},
        "luigi": {"2024-03-11": 4},
    })
    assert database.get_rank(chat_id, "month", "03-2024") == [("luigi", 4), ("mario", 3)]
    assert database.get_rank(chat_id, "month", "3-2024") == [("luigi", 4), ("mario", 3)]
    assert database.get_rank(chat_id, "year", "2024") == [("mario", 8), ("luigi", 4)]
    assert database.get_rank(chat_id, "month", "05-2024") == []


def test_get_statistics_closed_month(seed, chat_id):
    # February 2024 (leap year, 29 days): 3 days with counts 1, 2, 3
    seed({"mario": {"2024-02-01": 1, "2024-02-02": 2, "2024-02-03": 3}})
    (stat,) = database.get_statistics(chat_id, "month", "02-2024")
    assert stat["username"] == "mario"
    assert stat["mean"] == round(6 / 29, 2)
    assert stat["median"] == 0
    assert stat["variance"] > 0


def test_get_record_is_sorted_by_date(seed, chat_id):
    seed({"mario": {"2024-03-10": 1, "2024-01-05": 2}})
    assert database.get_record("mario", chat_id) == [("2024-01-05", 2), ("2024-03-10", 1)]


def test_constipation_days(seed, chat_id):
    today = datetime.today().date()
    seed({"mario": {(today - timedelta(days=0)).strftime("%Y-%m-%d"): 1}})
    assert database.get_constipation_days("mario", chat_id) == 0
    assert database.get_constipation_days("sconosciuto", chat_id) is None
