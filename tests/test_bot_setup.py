"""Bot setup: BOT_USERNAME, error handler, polling."""
import asyncio
import logging
import runpy

import pytest
from telegram.ext import Application

import caccometro
from conftest import make_context, make_update


def run(coro):
    return asyncio.run(coro)


def test_bot_mention_is_case_insensitive(monkeypatch):
    monkeypatch.setattr(caccometro, "BOT_USERNAME", "@CaccoMetro_Bot")
    upd = make_update(text="ciao @caccometro_bot come va")
    run(caccometro.handle_message(upd, make_context()))
    assert upd.message.reply_text.call_args[0][0] == "Cosa vuoi dirmi?"


def test_missing_bot_username_does_not_crash(monkeypatch):
    monkeypatch.setattr(caccometro, "BOT_USERNAME", None)
    upd = make_update(text="ciao a tutti")
    run(caccometro.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()


def test_error_handler_logs_traceback(caplog):
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        ctx = make_context()
        ctx.error = exc
        with caplog.at_level(logging.ERROR, logger="caccometro"):
            run(caccometro.error(make_update(), ctx))
    record = caplog.records[-1]
    assert record.exc_info is not None
    assert "boom" in record.getMessage()


def test_polling_receives_a_list_of_allowed_updates(monkeypatch):
    captured = {}

    def fake_run_polling(self, *args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(Application, "run_polling", fake_run_polling)
    monkeypatch.setenv("RUN_MODE", "POLLING")
    runpy.run_path(caccometro.__file__, run_name="__main__")
    assert captured["allowed_updates"] == ["message"]
