"""One line per update with command, chat type, duration, attempts and outcome; no names, no text (#168)."""
import json
import logging
import re

import httpx
import pytest
from telegram.request import HTTPXRequest

from caccometro import bot, webhook
from test_robust_sending import network_error
from conftest import BOT_USER
from test_webhook_identity import SECRET, message_dict, telegram_calls, telegram_update  # noqa: F401  (fixture)

DONE = re.compile(r"Update (\d+) done: command=(\S+) chat=(\w+) ms=(\d+) attempts=(\d+) outcome=(\w+)$")


def post(update, caplog):
    """POST an update to the webhook and return the 'done' lines that were logged.

    Args:
        update (dict): the update.
        caplog (pytest.LogCaptureFixture): pytest's fixture.

    Returns:
        list: the groups of each 'done' line.
    """
    pytest.importorskip("asgiref")   # Flask async views need it
    with caplog.at_level(logging.INFO, logger="caccometro"):
        assert webhook.app.test_client().post("/webhook", headers=SECRET, json=update).status_code == 200
    lines = [DONE.match(r.getMessage()) for r in caplog.records]
    return [m.groups() for m in lines if m]


def command(text, update_id):
    """The update of a command.

    Args:
        text (str): the text, starting with the command.
        update_id (int): the update ID.

    Returns:
        dict: the update.
    """
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
    """sendMessage fails with a proxy 503 `failures` times, getMe `me_failures` times, then they work (fresh process).

    Args:
        monkeypatch (pytest.MonkeyPatch): pytest's fixture.

    Returns:
        object: the state, with those counters and the calls made.
    """
    state = type("State", (), {"failures": 0, "calls": 0, "me_failures": 0, "me_calls": 0})()

    async def fake_do_request(self, url, method, *args, **kwargs):
        if url.endswith("getMe"):
            state.me_calls += 1
            if state.me_calls <= state.me_failures:
                raise network_error(httpx.ProxyError("503 Service Unavailable"))
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
    assert post(telegram_update(update_id=303), caplog)[0][4:] == ("4", "ok")  # getMe of the fresh process + 3


def test_a_reply_lost_after_all_the_attempts_is_marked_lost(flaky_telegram, caplog):
    flaky_telegram.failures = 6
    assert post(telegram_update(update_id=304), caplog)[0][4:] == ("7", "lost")  # getMe + 6
    assert 'Update "304" caused error' in caplog.text and caplog.text.count(" in message") == 1


def test_kinds_of_update():
    from conftest import make_update
    assert bot._update_kind(object()) == "other"
    upd = make_update(text="/classifica_mese 3-2026")
    assert bot._update_kind(upd) == "/leaderboard_month"
    assert bot._update_kind(make_update(text="/nonexistent")) == "message"


def test_the_startup_getme_and_its_retries_are_in_the_line(flaky_telegram, caplog):
    flaky_telegram.me_failures = 2
    assert post(telegram_update(update_id=305), caplog)[0][4:] == ("4", "ok")  # getMe 3 times + the reply


def test_an_update_lost_on_the_startup_getme_still_has_its_line(flaky_telegram, caplog):
    pytest.importorskip("asgiref")
    flaky_telegram.me_failures = 6
    with caplog.at_level(logging.INFO, logger="caccometro"):
        response = webhook.app.test_client().post("/webhook", headers=SECRET, json=telegram_update(update_id=306))
    assert response.status_code == 500
    assert "Update 306 done: command=message chat=group" in caplog.text
    assert "attempts=6 outcome=lost" in caplog.text


def test_an_update_refused_because_the_start_failed_is_processed_when_sent_again(flaky_telegram, caplog):
    flaky_telegram.me_failures = 6
    post_status = lambda: webhook.app.test_client().post("/webhook", headers=SECRET, json=telegram_update(update_id=308)).status_code
    pytest.importorskip("asgiref")
    assert post_status() == 500
    assert post(telegram_update(update_id=308), caplog)[-1][5] == "ok"  # counted, not ignored as already processed


def test_an_update_sent_again_writes_no_second_line(telegram_calls, caplog):  # noqa: F811
    post(telegram_update(update_id=307), caplog)
    assert len(post(telegram_update(update_id=307), caplog)) == 1  # caplog keeps the line of the first one
