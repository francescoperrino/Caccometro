"""Shared fixtures.

Note: `utils.py` calls locale.setlocale('it_IT.UTF-8') at import time, which fails
on hosts without that locale. Until the code is fixed we neutralise it
here, so the tests run anywhere.
"""
import locale
import os
import sys
import zlib
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


def uid(name):
    """Stable fake Telegram user ID for a test user name."""
    return zlib.crc32(name.encode("utf-8"))


@pytest.fixture
def seed(chat_id):
    """seed({'mario': {'2024-01-01': 1, ...}, ...}) registers the users and their counts.

    A user with no days (e.g. 'luigi': {}) is registered without counts.
    """
    def _seed(data):
        for name, days in data.items():
            database.upsert_user(chat_id, uid(name), name, name.capitalize())
            for date, count in days.items():
                database.update_count(uid(name), date, count, chat_id)
    return _seed


def make_tg_user(username="mario", user_id=None, full_name=None, is_bot=False):
    """Fake telegram.User."""
    if user_id is None:
        user_id = uid(username or full_name or "anonimo")
    if full_name is None:
        full_name = username.capitalize() if username else "Utente"
    return SimpleNamespace(id=user_id, username=username, full_name=full_name,
                           first_name=full_name.split()[0], is_bot=is_bot)


def make_update(text=None, username="mario", user_id=None, chat_id=CHAT_ID,
                sticker_emoji=None, has_from_user=True, full_name=None,
                reply_to=None, is_bot=False, chat_type="group"):
    """Fake Telegram Update, enough for the bot handlers.

    reply_to: a make_tg_user(...) of the author of the message being replied to.
    """
    chat = SimpleNamespace(type=chat_type, effective_name="Gruppo test")
    from_user = (make_tg_user(username, user_id, full_name, is_bot) if has_from_user else None)
    message = SimpleNamespace(
        text=text,
        from_user=from_user,
        chat_id=chat_id,
        chat=chat,
        sticker=SimpleNamespace(emoji=sticker_emoji) if sticker_emoji else None,
        reply_to_message=SimpleNamespace(from_user=reply_to) if reply_to is not None else None,
        reply_text=AsyncMock(),
        reply_photo=AsyncMock(),
    )
    return SimpleNamespace(
        message=message,
        update_id=1,
        _effective_message=message,
        effective_message=message,
    )


def make_context(*args, member_status="member"):
    """Fake CallbackContext; context.bot.get_chat_member returns a member with member_status."""
    bot = SimpleNamespace(get_chat_member=AsyncMock(return_value=SimpleNamespace(status=member_status)))
    return SimpleNamespace(args=list(args), bot=bot)
