"""Replies survive the intermittent network errors towards Telegram (issue #35)."""
import asyncio

import httpx
import pytest
from telegram.error import NetworkError, TimedOut
from telegram.request import HTTPXRequest

from caccometro import bot, chat, webhook
from caccometro import database
from conftest import CHAT_ID, make_update
from test_webhook_identity import SECRET, telegram_calls, telegram_update  # noqa: F401  (fixture)


class Attempts(list):
    """The calls made to the fake HTTP layer; `errors` are raised one per call, `sleeps` the waits asked for."""
    errors = ()


@pytest.fixture
def attempts(monkeypatch):
    """Fake HTTP layer: fails with the errors in `attempts.errors`, one per call, then succeeds.

    Args:
        monkeypatch (pytest.MonkeyPatch): pytest's fixture.

    Returns:
        Attempts: the calls, to inspect.
    """
    calls = Attempts()
    calls.sleeps = []

    async def fake_do_request(self, *args, **kwargs):
        calls.append(args)
        if len(calls) <= len(calls.errors):
            raise calls.errors[len(calls) - 1]
        return 200, b'{"ok": true, "result": true}'

    async def no_sleep(seconds):
        calls.sleeps.append(seconds)

    monkeypatch.setattr(HTTPXRequest, "do_request", fake_do_request)
    monkeypatch.setattr(bot.asyncio, "sleep", no_sleep)
    return calls


def network_error(cause):
    """A NetworkError as PTB raises it: the httpx error is its cause.

    Args:
        cause (Exception): the httpx error.

    Returns:
        NetworkError: the error.
    """
    error = TimedOut() if isinstance(cause, httpx.TimeoutException) else NetworkError(f"httpx.{type(cause).__name__}")
    error.__cause__ = cause
    return error


def send(request):
    """Send a request through a request object, as the library does.

    Args:
        request: the request object.

    Returns:
        The result of do_request.
    """
    return asyncio.run(request.do_request("https://api.telegram.org/x", "POST"))


def test_a_proxy_error_burst_longer_than_15_seconds_is_retried_and_the_request_succeeds(attempts):
    attempts.errors = [network_error(httpx.ProxyError("503 Service Unavailable"))] * 5
    assert send(bot._RetryingRequest())[0] == 200
    assert len(attempts) == 6
    assert attempts.sleeps == [1, 2, 4, 8, 16]


def test_after_six_failures_the_error_is_raised(attempts):
    attempts.errors = [network_error(httpx.ConnectError("refused"))] * 6
    with pytest.raises(NetworkError):
        send(bot._RetryingRequest())
    assert len(attempts) == 6


@pytest.mark.parametrize("cause", [httpx.ReadTimeout("slow"), httpx.ReadError("connection dropped")])
def test_errors_after_sending_are_not_retried_because_the_message_may_be_delivered(attempts, cause):
    attempts.errors = [network_error(cause)]
    with pytest.raises(NetworkError):
        send(bot._RetryingRequest())
    assert len(attempts) == 1


def test_the_bot_uses_the_retrying_request():
    assert isinstance(bot.application.bot.request, bot._RetryingRequest)


def test_an_update_sent_twice_is_counted_once(telegram_calls):  # noqa: F811
    pytest.importorskip("asgiref")   # Flask async views need it
    client = webhook.app.test_client()
    for _ in range(2):
        response = client.post("/webhook", headers=SECRET, json=telegram_update(update_id=7))
        assert response.status_code == 200
    assert telegram_calls.count("sendMessage") == 1
    today = database.now_rome().strftime("%Y-%m-%d")
    assert database.get_count(42, today, CHAT_ID) == 1


def test_a_caption_too_long_goes_in_a_separate_message(tmp_path):
    chart = b"png"
    upd = make_update()
    long_text = "x" * 1025
    asyncio.run(chat.reply_chart(upd, chart, long_text))
    assert "caption" not in upd.message.reply_photo.call_args.kwargs
    assert upd.message.reply_text.call_args[0][0] == long_text


def test_emojis_count_twice_in_the_caption_length(tmp_path):
    chart = b"png"
    upd = make_update()
    text = "💩" * 513       # 513 characters for Python, 1026 for Telegram
    asyncio.run(chat.reply_chart(upd, chart, text))
    assert "caption" not in upd.message.reply_photo.call_args.kwargs
    assert upd.message.reply_text.call_args[0][0] == text
