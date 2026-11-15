"""Chart edge cases."""
from datetime import date

import pytest

from caccometro import database
from caccometro.analysis import period_statistics
from caccometro import charts
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
    charts.generate_rank_chart(rank, {uid("mario"): days}, "year", str(year))
    daily = {d for d in days.requested if len(d) == 10}
    expected_days = 366 if year == 2024 else 365
    assert len(daily) == expected_days
    assert last_day in daily
    assert all(d.startswith(str(year)) for d in daily)  # no January 1st of the following year


def test_statistics_chart_with_zero_variance_does_not_crash(seed, chat_id):
    # First day of the month: a single observed day => zero variance for everyone
    seed({"mario": {"2024-03-01": 1}, "luigi": {"2024-03-01": 2}})
    stats = [
        {"user": database.User(uid("mario"), "mario", "Mario"), "mean": 1.0, "median": 1.0, "variance": 0.0},
        {"user": database.User(uid("luigi"), "luigi", "Luigi"), "mean": 2.0, "median": 2.0, "variance": 0.0},
    ]
    daily = {uid("mario"): {"2024-03-01": 1}, uid("luigi"): {"2024-03-01": 2}}
    assert charts.generate_statistics_chart(stats, daily, "month", "03-2024").startswith(b"\x89PNG")


def test_statistics_chart_with_all_zero_counts_does_not_crash(chat_id):
    stats = [{"user": database.User(uid("mario"), "mario", "Mario"), "mean": 0.0, "median": 0.0, "variance": 0.0}]
    assert charts.generate_statistics_chart(stats, {}, "month", "03-2024").startswith(b"\x89PNG")


def test_charts_accept_names_with_dollar_signs_and_equal_names(seed, chat_id):
    # '$' would start a math expression in matplotlib; two users may share the same display name
    for user_id, day in ((1, "2024-03-01"), (2, "2024-03-02")):
        database.upsert_user(chat_id, user_id, None, "Pay $$ me")
        database.add_count(user_id, day, 1, chat_id)
    rank = database.get_rank(chat_id, "month", "03-2024")
    daily = database.get_daily_counts(chat_id, "month", "03-2024")
    assert charts.generate_rank_chart(rank, daily, "month", "03-2024").startswith(b"\x89PNG")
    stats = period_statistics(daily, database.get_users(chat_id), "2024-03-01", "2024-03-31", date(2024, 4, 1))
    assert charts.generate_statistics_chart(stats, daily, "month", "03-2024").startswith(b"\x89PNG")


def test_month_names_are_italian_whatever_the_locale(monkeypatch):
    titles = []
    monkeypatch.setattr(charts, "png_bytes", lambda fig: titles.append(fig._suptitle.get_text() if fig._suptitle else
                                                                    " ".join(a.get_title() for a in fig.axes)))
    rank = [(database.User(uid("mario"), "mario", "Mario"), 1)]
    charts.generate_rank_chart(rank, {uid("mario"): {"2024-11-10": 1}}, "month", "11-2024")
    assert "Novembre 2024" in titles[0]


def test_charts_never_touch_the_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rank = [(database.User(uid("mario"), "mario", "Mario"), 1)]
    charts.generate_rank_chart(rank, {uid("mario"): {"2024-03-10": 1}}, "month", "03-2024")
    assert list(tmp_path.rglob("*.png")) == []
