"""Shared fixtures.

Note: `utils.py` calls locale.setlocale('it_IT.UTF-8') at import time, which fails
on hosts without that locale. Until the code is fixed we neutralise it
here, so the tests run anywhere.
"""
import locale
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("BOT_TOKEN", "123456:TEST-TOKEN")
os.environ.setdefault("BOT_USERNAME", "@caccometro_test_bot")
os.environ.setdefault("RUN_MODE", "POLLING")

locale.setlocale = lambda *args, **kwargs: "C"  # noqa: E731

import database  # noqa: E402
import utils  # noqa: E402
import caccometro  # noqa: E402

CHAT_ID = -1001


@pytest.fixture
def chat_id():
    return CHAT_ID


@pytest.fixture(autouse=True)
def isolated_folders(tmp_path, monkeypatch):
    """DB and charts go to a temporary folder, never to the real ones."""
    db_dir = tmp_path / "db"
    charts_dir = tmp_path / "charts"
    charts_dir.mkdir()
    for module in (database, utils, caccometro):
        if hasattr(module, "DB_FOLDER"):
            monkeypatch.setattr(module, "DB_FOLDER", str(db_dir))
        if hasattr(module, "CHARTS_FOLDER"):
            monkeypatch.setattr(module, "CHARTS_FOLDER", str(charts_dir))
    database.init_database(CHAT_ID)
    return tmp_path


@pytest.fixture
def seed(chat_id):
    """seed({'mario': {'2024-01-01': 1, ...}, ...})"""
    def _seed(data):
        for username, days in data.items():
            for date, count in days.items():
                database.update_count(username, date, count, chat_id)
    return _seed


def make_update(text=None, username="mario", user_id=1, chat_id=CHAT_ID,
                sticker_emoji=None, has_from_user=True):
    """Fake Telegram Update, enough for the bot handlers."""
    chat = SimpleNamespace(type="group", effective_name="Gruppo test")
    from_user = (
        SimpleNamespace(id=user_id, username=username, first_name="Mario")
        if has_from_user else None
    )
    message = SimpleNamespace(
        text=text,
        from_user=from_user,
        chat_id=chat_id,
        chat=chat,
        sticker=SimpleNamespace(emoji=sticker_emoji) if sticker_emoji else None,
        reply_text=AsyncMock(),
        reply_photo=AsyncMock(),
    )
    return SimpleNamespace(
        message=message,
        update_id=1,
        _effective_message=message,
        effective_message=message,
    )


def make_context(*args):
    return SimpleNamespace(args=list(args))
