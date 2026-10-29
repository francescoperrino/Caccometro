"""Characterization tests for the handlers (happy path)."""
import asyncio
from datetime import datetime

import pytz

import caccometro
import database
from conftest import make_context, make_update, uid


def run(coro):
    return asyncio.run(coro)


def today_rome():
    return datetime.now(pytz.timezone("Europe/Rome")).strftime("%Y-%m-%d")


def test_poop_message_increments_count(chat_id):
    upd = make_update(text="💩")
    run(caccometro.handle_message(upd, make_context()))
    run(caccometro.handle_message(make_update(text="ho fatto 💩"), make_context()))
    assert database.get_count(uid("mario"), today_rome(), chat_id) == 2
    assert "Complimenti @mario" in upd.message.reply_text.call_args[0][0]


def test_poop_sticker_increments_count(chat_id):
    run(caccometro.handle_message(make_update(sticker_emoji="💩"), make_context()))
    assert database.get_count(uid("mario"), today_rome(), chat_id) == 1


def test_plain_message_is_ignored(chat_id):
    upd = make_update(text="ciao a tutti")
    run(caccometro.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()
    assert database.get_count(uid("mario"), today_rome(), chat_id) == 0


def test_aggiungi_and_togli(chat_id, seed):
    seed({"luigi": {}})
    run(caccometro.aggiungi_command(make_update(), make_context("@luigi", "10-03-2024")))
    run(caccometro.aggiungi_command(make_update(), make_context("@luigi", "10-03-2024")))
    assert database.get_count(uid("luigi"), "2024-03-10", chat_id) == 2
    run(caccometro.togli_command(make_update(), make_context("@luigi", "10-03-2024")))
    assert database.get_count(uid("luigi"), "2024-03-10", chat_id) == 1


def test_conto_giorno_reply(chat_id, seed):
    seed({"luigi": {"2024-03-10": 2}})
    upd = make_update()
    run(caccometro.conto_giorno_command(upd, make_context("@luigi", "10-03-2024")))
    assert "2" in upd.message.reply_text.call_args[0][0]


def test_classifica_mese_sends_chart_and_text(seed):
    seed({"mario": {"2024-03-10": 2}, "luigi": {"2024-03-11": 4}})
    upd = make_update()
    run(caccometro.classifica_mese_command(upd, make_context("03-2024")))
    upd.message.reply_photo.assert_called_once()
    text = upd.message.reply_text.call_args[0][0]
    assert text.index("luigi") < text.index("mario")


def test_statistiche_mese_sends_chart_and_text(seed):
    seed({"mario": {"2024-03-10": 2, "2024-03-12": 1}, "luigi": {"2024-03-11": 4}})
    upd = make_update()
    run(caccometro.statistiche_mese_command(upd, make_context("03-2024")))
    upd.message.reply_photo.assert_called_once()
    assert "Media" in upd.message.reply_text.call_args[0][0]


def test_record_happy_path(seed):
    seed({"mario": {"2024-01-01": 1, "2024-01-02": 2, "2024-02-10": 3, "2024-03-01": 1}})
    upd = make_update()
    run(caccometro.record_command(upd, make_context()))
    assert "Record per @mario" in upd.message.reply_text.call_args[0][0]
