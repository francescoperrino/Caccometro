"""Fixes for the /record command."""
import asyncio
from datetime import datetime

import pytz

import caccometro
from conftest import make_context, make_update


def run(coro):
    return asyncio.run(coro)


def record_text(username="mario"):
    upd = make_update(username=username)
    run(caccometro.record_command(upd, make_context()))
    return upd.message.reply_text.call_args[0][0]


def test_record_with_data_only_in_current_month_does_not_crash(seed):
    today = datetime.now(pytz.timezone("Europe/Rome")).strftime("%Y-%m-%d")
    seed({"mario": {today: 1}})
    text = record_text()
    assert "Record per @mario" in text
    assert "None" not in text


def test_record_single_month_uses_singular(seed):
    seed({"mario": {"2024-01-01": 2, "2024-02-01": 1, "2024-03-01": 1}})
    text = record_text()
    assert "nel mese 01-2024" in text
    assert "nei mesi" not in text.split("🤩")[1].split("\n")[0]


def test_record_multiple_tied_months_uses_plural(seed):
    seed({"mario": {"2024-01-01": 2, "2024-02-01": 2, "2024-03-01": 1}})
    text = record_text()
    assert "nei mesi 01-2024, 02-2024" in text


def test_record_streak_count_line_does_not_reuse_longest_streak_length(seed):
    # Longest streak: 3 days of 1 (total 3). Streak with most 💩: 2 days of 5 (total 10).
    seed({"mario": {
        "2024-01-01": 1, "2024-01-02": 1, "2024-01-03": 1,
        "2024-02-10": 5, "2024-02-11": 5,
    }})
    text = record_text()
    count_line = [l for l in text.split("\n") if l.startswith("🫣")][0]
    assert "10 volte" in count_line
    assert "3 giorni" not in count_line
    assert "10-02-2024 - 11-02-2024" in count_line
