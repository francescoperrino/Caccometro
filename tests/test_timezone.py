"""Every "today" computation must use Europe/Rome, not the server timezone (UTC)."""
from datetime import datetime

import database
import utils
from conftest import uid


def test_now_rome_is_naive_and_in_rome_time():
    now = database.now_rome()
    assert now.tzinfo is None


def test_constipation_days_uses_rome_today(seed, chat_id, monkeypatch):
    seed({"mario": {"2024-03-10": 1}})
    monkeypatch.setattr(database, "now_rome", lambda: datetime(2024, 3, 13, 0, 30))
    assert database.get_constipation_days(uid("mario"), chat_id) == 3


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


def test_record_uses_rome_today_for_the_current_month_and_status(seed, monkeypatch):
    """/record decides "today" and "the current month" with the Rome date, not the server date."""
    import asyncio
    import caccometro
    from conftest import make_context, make_update

    seed({"mario": {"2024-03-10": 2, "2024-04-01": 1}})
    monkeypatch.setattr(caccometro, "now_rome", lambda: datetime(2024, 4, 1, 0, 30))
    upd = make_update()
    asyncio.run(caccometro.record_command(upd, make_context()))
    text = upd.message.reply_text.call_args[0][0]
    assert "↳ Oggi: 1" in text                      # April 1st is "today" in Rome
    assert "nel mese 03-2024" in text               # March is completed, April is the current month
