"""Every "today" computation must use Europe/Rome, not the server timezone (UTC)."""
import asyncio
from datetime import datetime, timezone

from caccometro import commands, database, messages
from conftest import make_context, make_update, uid


def test_now_rome_is_naive_and_in_rome_time():
    now = database.now_rome()
    assert now.tzinfo is None


def test_constipation_days_uses_rome_today(seed, chat_id, monkeypatch):
    seed({"mario": {"2024-03-10": 1}})
    monkeypatch.setattr(database, "now_rome", lambda: datetime(2024, 3, 13, 0, 30))
    assert database.get_constipation_days(uid("mario"), chat_id) == 3


def statistics_caption(command, monkeypatch, now):
    monkeypatch.setattr(commands, "now_rome", lambda: now)
    upd = make_update()
    asyncio.run(command(upd, make_context()))
    return upd.message.reply_photo.call_args.kwargs["caption"]


def test_statistics_current_month_uses_rome_today(seed, monkeypatch):
    # "Today" in Rome is March 10, 2024: the current month has 10 valid days, not 31
    seed({"mario": {"2024-03-02": 5}})
    caption = statistics_caption(commands.statistiche_mese_command, monkeypatch, datetime(2024, 3, 10, 0, 30))
    assert ": 0.50 ·" in caption  # mean 5 / 10


def test_statistics_current_year_uses_rome_today(seed, monkeypatch):
    seed({"mario": {"2024-01-02": 4}})
    caption = statistics_caption(commands.statistiche_anno_command, monkeypatch, datetime(2024, 1, 10, 0, 30))
    assert ": 0.40 ·" in caption  # mean 4 / 10


def test_record_uses_rome_today_for_the_current_month_and_status(seed, monkeypatch):
    """/record decides "today" and "the current month" with the Rome date, not the server date."""

    seed({"mario": {"2024-03-10": 2, "2024-04-01": 1}})
    monkeypatch.setattr(commands, "now_rome", lambda: datetime(2024, 4, 1, 0, 30))
    upd = make_update()
    asyncio.run(commands.record_command(upd, make_context("io")))
    text = upd.message.reply_text.call_args[0][0]
    assert "↳ Oggi: 1" in text                      # April 1st is "today" in Rome
    assert "nel mese 03-2024" in text               # March is completed, April is the current month


def test_late_processed_poop_counts_on_the_day_it_was_sent(chat_id, monkeypatch):
    monkeypatch.setattr(messages, "now_rome", lambda: datetime(2026, 11, 17, 0, 5))
    sent = datetime(2026, 11, 16, 22, 59, tzinfo=timezone.utc)   # 23:59 in Rome (CET)
    upd = make_update(text="💩", date=sent)
    asyncio.run(messages.handle_message(upd, make_context()))
    assert database.get_count(uid("mario"), "2026-11-16", chat_id) == 1
    assert database.get_count(uid("mario"), "2026-11-17", chat_id) == 0


def test_poop_sent_after_midnight_in_summer_counts_on_the_new_day(chat_id):
    sent = datetime(2026, 7, 15, 22, 30, tzinfo=timezone.utc)   # 00:30 of the 16th in Rome (CEST)
    messages.record_poop(database.User(uid("mario"), "mario", "Mario"), chat_id, sent)
    assert database.get_count(uid("mario"), "2026-07-16", chat_id) == 1
