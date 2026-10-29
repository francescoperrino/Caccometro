"""Chart edge cases."""
import os

import pytest

import database
import utils


@pytest.fixture
def requested_dates(monkeypatch):
    """Record the dates requested from get_count by the charts."""
    calls = []
    real = database.get_count

    def spy(username, date, chat_id):
        calls.append(date)
        return real(username, date, chat_id)

    monkeypatch.setattr(utils, "get_count", spy)
    return calls


@pytest.mark.parametrize("year,last_day", [(2025, "2025-12-31"), (2024, "2024-12-31")])
def test_year_rank_chart_covers_exactly_the_days_of_the_year(
        seed, chat_id, requested_dates, year, last_day):
    seed({"mario": {f"{year}-03-10": 1}})
    utils.generate_rank_chart([("mario", 1)], chat_id, "year", str(year))
    daily = {d for d in requested_dates if len(d) == 10}
    expected_days = 366 if year == 2024 else 365
    assert len(daily) == expected_days
    assert last_day in daily
    assert all(d.startswith(str(year)) for d in daily)  # no January 1st of the following year


def test_statistics_chart_with_zero_variance_does_not_crash(seed, chat_id, isolated_folders):
    # First day of the month: a single observed day => zero variance for everyone
    seed({"mario": {"2024-03-01": 1}, "luigi": {"2024-03-01": 2}})
    stats = [
        {"username": "mario", "mean": 1.0, "median": 1.0, "variance": 0.0},
        {"username": "luigi", "mean": 2.0, "median": 2.0, "variance": 0.0},
    ]
    utils.generate_statistics_chart(stats, chat_id, "month", "03-2024")
    assert os.path.exists(isolated_folders / "charts" / f"{chat_id}_2024_03_stats.png")


def test_statistics_chart_with_all_zero_counts_does_not_crash(chat_id, isolated_folders):
    stats = [{"username": "mario", "mean": 0.0, "median": 0.0, "variance": 0.0}]
    utils.generate_statistics_chart(stats, chat_id, "month", "03-2024")
    assert os.path.exists(isolated_folders / "charts" / f"{chat_id}_2024_03_stats.png")
