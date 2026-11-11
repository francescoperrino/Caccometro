"""The webhook must not ask Telegram 'who am I?' (getMe) for every update."""
import asyncio

import pytest
from telegram import Update
from telegram.error import NetworkError
from telegram.ext import Application
from unittest.mock import AsyncMock

import caccometro
import database
from conftest import CHAT_ID

BOT_USER = {"id": 7, "is_bot": True, "first_name": "Caccometro", "username": "caccometro_test_bot"}


def message_dict(text="ok"):
    return {"message_id": 2, "date": 1700000000, "text": text,
            "chat": {"id": CHAT_ID, "type": "group", "title": "g"}}


def telegram_update(text="💩", update_id=1, user_id=42, username="mario"):
    return {"update_id": update_id,
            "message": {"message_id": update_id, "date": 1700000000, "text": text,
                        "chat": {"id": CHAT_ID, "type": "group", "title": "g"},
                        "from": {"id": user_id, "is_bot": False, "first_name": "Mario", "username": username}}}


@pytest.fixture
def telegram_calls(monkeypatch):
    """Replace the HTTP layer of the bot: records the API methods called, answers like Telegram."""
    calls = []

    async def fake_post(endpoint, data=None, **kwargs):
        calls.append(endpoint)
        if endpoint == "getMe":
            return BOT_USER
        return message_dict()

    monkeypatch.setattr(caccometro.application.bot, "_post", fake_post)
    monkeypatch.setattr(caccometro.application.bot, "_bot_user", None)   # fresh process
    return calls


def cycle(bot):
    """What the webhook does around every update."""
    asyncio.run(bot.initialize())
    asyncio.run(bot.shutdown())


def test_get_me_is_called_once_across_many_initialize_shutdown_cycles(telegram_calls):
    for _ in range(4):
        cycle(caccometro.application.bot)
    assert telegram_calls.count("getMe") == 1


def test_bot_identity_is_available_after_the_cached_initialize(telegram_calls):
    cycle(caccometro.application.bot)
    cycle(caccometro.application.bot)
    assert caccometro.application.bot.username == "caccometro_test_bot"


def test_a_failed_get_me_is_not_cached(monkeypatch):
    attempts = []

    async def flaky_post(endpoint, data=None, **kwargs):
        attempts.append(endpoint)
        if len(attempts) == 1:
            raise NetworkError("503 Service Unavailable")
        return BOT_USER

    monkeypatch.setattr(caccometro.application.bot, "_post", flaky_post)
    monkeypatch.setattr(caccometro.application.bot, "_bot_user", None)
    with pytest.raises(NetworkError):
        asyncio.run(caccometro.application.bot.initialize())
    cycle(caccometro.application.bot)          # the next update retries and succeeds
    assert attempts == ["getMe", "getMe"]


def test_two_webhook_requests_ask_getme_once_and_both_are_processed(telegram_calls):
    pytest.importorskip("asgiref")   # Flask async views need it
    client = caccometro.app.test_client()
    for update_id in (1, 2):
        response = client.post(f"/{caccometro.BOT_TOKEN}", json=telegram_update(update_id=update_id))
        assert response.status_code == 200
    assert telegram_calls.count("getMe") == 1
    assert telegram_calls.count("sendMessage") == 2
    today = database.now_rome().strftime("%Y-%m-%d")
    assert database.get_count(42, today, CHAT_ID) == 2


def test_webhook_command_with_bot_suffix_is_recognized(telegram_calls):
    """/cmd@botname needs the cached bot username to be matched."""
    pytest.importorskip("asgiref")   # Flask async views need it
    client = caccometro.app.test_client()
    client.post(f"/{caccometro.BOT_TOKEN}", json=telegram_update(text="💩", update_id=1))
    update = telegram_update(text="/costipazione@caccometro_test_bot", update_id=2)
    update["message"]["entities"] = [{"type": "bot_command", "offset": 0, "length": len("/costipazione@caccometro_test_bot")}]
    response = client.post(f"/{caccometro.BOT_TOKEN}", json=update)
    assert response.status_code == 200
    assert telegram_calls.count("sendMessage") == 2      # the 💩 reply and the /costipazione reply
