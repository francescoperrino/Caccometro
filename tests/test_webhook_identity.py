"""The webhook must not ask Telegram 'who am I?' (getMe) for every update."""
import asyncio
import time
from pathlib import Path

import pytest
from telegram.error import NetworkError
from unittest.mock import AsyncMock

from caccometro import bot, config, webhook
from caccometro import database
from conftest import BOT_USER, CHAT_ID

SECRET = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}   # as Telegram sends it



def message_dict(text="ok"):
    """The message Telegram answers to sendMessage.

    Args:
        text (str): the text.

    Returns:
        dict: the message.
    """
    return {"message_id": 2, "date": 1700000000, "text": text,
            "chat": {"id": CHAT_ID, "type": "group", "title": "g"}}


def telegram_update(text="💩", update_id=1, user_id=42, username="mario"):
    """The update Telegram posts to the webhook for a message.

    Args:
        text (str): the text.
        update_id (int): the update ID.
        user_id (int): the sender.
        username (str): the username of the sender.

    Returns:
        dict: the update.
    """
    return {"update_id": update_id,
            "message": {"message_id": update_id, "date": int(time.time()), "text": text,
                        "chat": {"id": CHAT_ID, "type": "group", "title": "g"},
                        "from": {"id": user_id, "is_bot": False, "first_name": "Mario", "username": username}}}


@pytest.fixture
def telegram_calls(monkeypatch):
    """Replace the HTTP layer of the bot: records the API methods called, answers like Telegram.

    Args:
        monkeypatch (pytest.MonkeyPatch): pytest's fixture.

    Returns:
        list: the methods called.
    """
    calls = []

    async def fake_post(endpoint, data=None, **kwargs):
        calls.append(endpoint)
        if endpoint == "getMe":
            return BOT_USER
        return message_dict()

    monkeypatch.setattr(bot.application.bot, "_post", fake_post)
    monkeypatch.setattr(bot.application.bot, "_bot_user", None)   # fresh process
    return calls


def cycle(bot):
    """What the webhook does around every update.

    Args:
        bot: the application bot, started and stopped.
    """
    asyncio.run(bot.initialize())
    asyncio.run(bot.shutdown())


def test_get_me_is_called_once_across_many_initialize_shutdown_cycles(telegram_calls):
    for _ in range(4):
        cycle(bot.application.bot)
    assert telegram_calls.count("getMe") == 1


def test_bot_identity_is_available_after_the_cached_initialize(telegram_calls):
    cycle(bot.application.bot)
    cycle(bot.application.bot)
    assert bot.application.bot.username == "caccometro_test_bot"


def test_a_failed_get_me_is_not_cached(monkeypatch):
    attempts = []

    async def flaky_post(endpoint, data=None, **kwargs):
        attempts.append(endpoint)
        if len(attempts) == 1:
            raise NetworkError("503 Service Unavailable")
        return BOT_USER

    monkeypatch.setattr(bot.application.bot, "_post", flaky_post)
    monkeypatch.setattr(bot.application.bot, "_bot_user", None)
    with pytest.raises(NetworkError):
        asyncio.run(bot.application.bot.initialize())
    cycle(bot.application.bot)          # the next update retries and succeeds
    assert attempts == ["getMe", "getMe"]


def test_two_webhook_requests_ask_getme_once_and_both_are_processed(telegram_calls):
    pytest.importorskip("asgiref")   # Flask async views need it
    client = webhook.app.test_client()
    for update_id in (1, 2):
        response = client.post("/webhook", headers=SECRET, json=telegram_update(update_id=update_id))
        assert response.status_code == 200
    assert telegram_calls.count("getMe") == 1
    assert telegram_calls.count("sendMessage") == 2
    today = database.now_rome().strftime("%Y-%m-%d")
    assert database.get_count(42, today, CHAT_ID) == 2


def test_webhook_command_with_bot_suffix_is_recognized(telegram_calls):
    """/cmd@botname needs the cached bot username to be matched."""
    pytest.importorskip("asgiref")   # Flask async views need it
    client = webhook.app.test_client()
    client.post("/webhook", headers=SECRET, json=telegram_update(text="💩", update_id=1))
    update = telegram_update(text="/last_poop@caccometro_test_bot", update_id=2)
    update["message"]["entities"] = [{"type": "bot_command", "offset": 0, "length": len("/last_poop@caccometro_test_bot")}]
    response = client.post("/webhook", headers=SECRET, json=update)
    assert response.status_code == 200
    assert telegram_calls.count("sendMessage") == 2      # the 💩 reply and the reply to /last_poop


@pytest.mark.parametrize("headers", [{}, {"X-Telegram-Bot-Api-Secret-Token": "wrong"}, {"X-Telegram-Bot-Api-Secret-Token": "caffé"}])
def test_a_call_without_the_right_secret_is_refused(telegram_calls, headers):
    pytest.importorskip("asgiref")   # Flask async views need it
    client = webhook.app.test_client()
    response = client.post("/webhook", headers=headers, json=telegram_update(update_id=9))
    assert response.status_code == 403
    assert telegram_calls == []
    today = database.now_rome().strftime("%Y-%m-%d")
    assert database.get_count(42, today, CHAT_ID) == 0


def test_the_old_path_with_the_token_is_gone(telegram_calls):
    pytest.importorskip("asgiref")   # Flask async views need it
    client = webhook.app.test_client()
    response = client.post(f"/{config.BOT_TOKEN}", headers=SECRET, json=telegram_update(update_id=10))
    assert response.status_code == 404


def test_webhook_errors_are_logged_with_the_traceback(telegram_calls, monkeypatch, caplog):
    pytest.importorskip("asgiref")   # Flask async views need it
    monkeypatch.setattr(bot.application, "process_update", AsyncMock(side_effect=RuntimeError("boom")))
    response = webhook.app.test_client().post("/webhook", headers=SECRET, json=telegram_update(update_id=11))
    assert response.status_code == 500
    assert any(r.exc_info and "boom" in str(r.exc_info[1]) for r in caplog.records)


def test_set_webhook_asks_only_for_message_updates(monkeypatch):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import set_webhook
    fake_bot = AsyncMock()
    monkeypatch.setattr(set_webhook, "Bot", lambda token: fake_bot)
    asyncio.run(set_webhook.main())
    assert fake_bot.set_webhook.call_args.kwargs["allowed_updates"] == ["message"]
