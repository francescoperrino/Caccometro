"""Characterization tests for the handlers (happy path)."""
import asyncio
from datetime import datetime

import pytz

from caccometro import commands, messages
from caccometro import database
from conftest import make_context, make_update, uid


def run(coro):
    return asyncio.run(coro)


def today_rome():
    return datetime.now(pytz.timezone("Europe/Rome")).strftime("%Y-%m-%d")


def test_poop_message_increments_count(chat_id):
    upd = make_update(text="💩")
    run(messages.handle_message(upd, make_context()))
    run(messages.handle_message(make_update(text="ho fatto 💩"), make_context()))
    assert database.get_count(uid("mario"), today_rome(), chat_id) == 2
    assert "Complimenti @mario" in upd.message.reply_text.call_args[0][0]


def test_poop_sticker_increments_count(chat_id):
    run(messages.handle_message(make_update(sticker_emoji="💩"), make_context()))
    assert database.get_count(uid("mario"), today_rome(), chat_id) == 1


def test_plain_message_is_ignored(chat_id):
    upd = make_update(text="ciao a tutti")
    run(messages.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()
    assert database.get_count(uid("mario"), today_rome(), chat_id) == 0


def test_start_shows_the_version(chat_id):
    upd = make_update()
    run(commands.start_command(upd, make_context()))
    assert f"Versione {commands.__version__}" in upd.message.reply_text.call_args[0][0]


def test_home_page_shows_the_version():
    from caccometro import webhook
    assert f"versione {webhook.__version__}." in webhook.app.test_client().get("/").get_data(as_text=True)


def test_aggiungi_and_togli(chat_id, seed):
    seed({"luigi": {}})
    admin = dict(member_status="administrator")   # changing the counts of somebody else
    run(commands.aggiungi_command(make_update(), make_context("@luigi", "10-03-2024", **admin)))
    run(commands.aggiungi_command(make_update(), make_context("@luigi", "10-03-2024", **admin)))
    assert database.get_count(uid("luigi"), "2024-03-10", chat_id) == 2
    run(commands.togli_command(make_update(), make_context("@luigi", "10-03-2024", **admin)))
    assert database.get_count(uid("luigi"), "2024-03-10", chat_id) == 1


def test_conto_giorno_reply(chat_id, seed):
    seed({"luigi": {"2024-03-10": 2}})
    upd = make_update()
    run(commands.conto_giorno_command(upd, make_context("@luigi", "10-03-2024")))
    assert "2" in upd.message.reply_text.call_args[0][0]


def test_classifica_mese_sends_chart_and_text(seed):
    seed({"mario": {"2024-03-10": 2}, "luigi": {"2024-03-11": 4}})
    upd = make_update()
    run(commands.classifica_mese_command(upd, make_context("03-2024")))
    upd.message.reply_photo.assert_called_once()
    text = upd.message.reply_photo.call_args.kwargs["caption"]   # one message: chart + caption
    assert text.index("luigi") < text.index("mario")


def test_statistiche_mese_sends_chart_and_text(seed):
    seed({"mario": {"2024-03-10": 2, "2024-03-12": 1}, "luigi": {"2024-03-11": 4}})
    upd = make_update()
    run(commands.statistiche_mese_command(upd, make_context("03-2024")))
    upd.message.reply_photo.assert_called_once()
    assert "media · mediana" in upd.message.reply_photo.call_args.kwargs["caption"]


def test_record_happy_path(seed):
    seed({"mario": {"2024-01-01": 1, "2024-01-02": 2, "2024-02-10": 3, "2024-03-01": 1}})
    upd = make_update()
    run(commands.record_command(upd, make_context("io")))
    assert "Record per @mario" in upd.message.reply_text.call_args[0][0]


def test_classifica_mese_shows_the_forecast_only_for_the_current_month(seed):
    seed({"mario": {today_rome(): 30}, "luigi": {"2024-03-11": 4}})
    upd = make_update()
    run(commands.classifica_mese_command(upd, make_context()))
    assert "previsione a fine mese" in upd.message.reply_photo.call_args.kwargs["caption"]
    assert "30 💩 → " in upd.message.reply_photo.call_args.kwargs["caption"]

    upd = make_update()
    run(commands.classifica_mese_command(upd, make_context("03-2024")))
    assert "→" not in upd.message.reply_photo.call_args.kwargs["caption"]


def test_start_without_a_message_does_nothing():
    """An edited /start has no update.message: it must not raise."""
    upd = make_update()
    upd.message = None
    run(commands.start_command(upd, make_context()))
