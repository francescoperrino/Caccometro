"""Chart edge cases."""
import os

import pytest

import database
import utils
from conftest import uid


class RecordingDays(dict):
    """Per-user {day: count} dict that records every day the chart looks up."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requested = set()

    def get(self, key, default=None):
        self.requested.add(key)
        return super().get(key, default)


@pytest.mark.parametrize("year,last_day", [(2025, "2025-12-31"), (2024, "2024-12-31")])
def test_year_rank_chart_covers_exactly_the_days_of_the_year(chat_id, year, last_day):
    days = RecordingDays({f"{year}-03-10": 1})
    rank = [(database.User(uid("mario"), "mario", "Mario"), 1)]
    utils.generate_rank_chart(rank, {uid("mario"): days}, chat_id, "year", str(year))
    daily = {d for d in days.requested if len(d) == 10}
    expected_days = 366 if year == 2024 else 365
    assert len(daily) == expected_days
    assert last_day in daily
    assert all(d.startswith(str(year)) for d in daily)  # no January 1st of the following year


def test_statistics_chart_with_zero_variance_does_not_crash(seed, chat_id, isolated_folders):
    # First day of the month: a single observed day => zero variance for everyone
    seed({"mario": {"2024-03-01": 1}, "luigi": {"2024-03-01": 2}})
    stats = [
        {"user": database.User(uid("mario"), "mario", "Mario"), "mean": 1.0, "median": 1.0, "variance": 0.0},
        {"user": database.User(uid("luigi"), "luigi", "Luigi"), "mean": 2.0, "median": 2.0, "variance": 0.0},
    ]
    daily = {uid("mario"): {"2024-03-01": 1}, uid("luigi"): {"2024-03-01": 2}}
    utils.generate_statistics_chart(stats, daily, chat_id, "month", "03-2024")
    assert os.path.exists(isolated_folders / "charts" / f"{chat_id}_2024_03_stats.png")


def test_statistics_chart_with_all_zero_counts_does_not_crash(chat_id, isolated_folders):
    stats = [{"user": database.User(uid("mario"), "mario", "Mario"), "mean": 0.0, "median": 0.0, "variance": 0.0}]
    utils.generate_statistics_chart(stats, {}, chat_id, "month", "03-2024")
    assert os.path.exists(isolated_folders / "charts" / f"{chat_id}_2024_03_stats.png")


def test_charts_accept_names_with_dollar_signs_and_equal_names(seed, chat_id, isolated_folders):
    # '$' would start a math expression in matplotlib; two users may share the same display name
    for user_id, day in ((1, "2024-03-01"), (2, "2024-03-02")):
        database.upsert_user(chat_id, user_id, None, "Pay $$ me")
        database.update_count(user_id, day, 1, chat_id)
    rank = database.get_rank(chat_id, "month", "03-2024")
    daily = database.get_daily_counts(chat_id, "month", "03-2024")
    utils.generate_rank_chart(rank, daily, chat_id, "month", "03-2024")
    assert os.path.exists(isolated_folders / "charts" / f"{chat_id}_2024_03_chart.png")
    utils.generate_statistics_chart(database.get_statistics(chat_id, "month", "03-2024"), daily,
                                    chat_id, "month", "03-2024")
    assert os.path.exists(isolated_folders / "charts" / f"{chat_id}_2024_03_stats.png")
