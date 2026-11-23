"""One line per update with command, chat type, duration, attempts and outcome; no names, no text (#168)."""
import json
import logging
import re

import httpx
import pytest
from telegram.request import HTTPXRequest

from caccometro import bot, webhook
from test_robust_sending import network_error
from test_webhook_identity import BOT_USER, SECRET, message_dict, telegram_calls, telegram_update  # noqa: F401  (fixture)

DONE = re.compile(r"Update (\d+) done: command=(\S+) chat=(\w+) ms=(\d+) attempts=(\d+) outcome=(\w+)$")


def post(update, caplog):
    pytest.importorskip("asgiref")   # Flask async views need it
    with caplog.at_level(logging.INFO, logger="caccometro"):
        assert webhook.app.test_client().post("/webhook", headers=SECRET, json=update).status_code == 200
    lines = [DONE.match(r.getMessage()) for r in caplog.records]
    return [m.groups() for m in lines if m]


def command(text, update_id):
    update = telegram_update(text=text, update_id=update_id)
    update["message"]["entities"] = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]
    return update


def test_a_poop_writes_one_line_without_names_or_text(telegram_calls, caplog):  # noqa: F811
    lines = post(telegram_update(text="💩 segreto", update_id=301), caplog)
    assert [line[:3] for line in lines] == [("301", "message", "group")]
    assert lines[0][5] == "ok"
    assert "mario" not in caplog.text and "segreto" not in caplog.text


def test_an_italian_command_is_logged_with_its_english_name(telegram_calls, caplog):  # noqa: F811
    lines = post(command("/ultima_cacca@caccometro_test_bot", 302), caplog)
    assert lines[0][1] == "/last_poop"


@pytest.fixture
def flaky_telegram(monkeypatch):
    """sendMessage fails with a proxy 503 `flaky_telegram.failures` times, then works; getMe always works."""
    state = type("State", (), {"failures": 0, "calls": 0})()

    async def fake_do_request(self, url, method, *args, **kwargs):
        if url.endswith("getMe"):
            return 200, json.dumps({"ok": True, "result": BOT_USER}).encode()
        state.calls += 1
        if state.calls <= state.failures:
            raise network_error(httpx.ProxyError("503 Service Unavailable"))
        return 200, json.dumps({"ok": True, "result": message_dict()}).encode()

    async def no_sleep(seconds):
        pass

    monkeypatch.setattr(HTTPXRequest, "do_request", fake_do_request)
    monkeypatch.setattr(bot.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(bot.application.bot, "_bot_user", None)
    return state


def test_retries_are_counted_in_the_attempts(flaky_telegram, caplog):
    flaky_telegram.failures = 2
    assert post(telegram_update(update_id=303), caplog)[0][4:] == ("3", "ok")


def test_a_reply_lost_after_all_the_attempts_is_marked_lost(flaky_telegram, caplog):
    flaky_telegram.failures = 6
    assert post(telegram_update(update_id=304), caplog)[0][4:] == ("6", "lost")
    assert 'Update "304" caused error' in caplog.text and caplog.text.count(" in message") == 1


def test_kinds_of_update():
    from conftest import make_update
    assert bot.update_kind(object()) == "other"
    upd = make_update(text="/classifica_mese 3-2026")
    assert bot.update_kind(upd) == "/leaderboard_month"
    assert bot.update_kind(make_update(text="/nonexistent")) == "message"
