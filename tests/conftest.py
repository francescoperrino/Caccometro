"""Shared fixtures."""
import asyncio
import os
import sqlite3
import sys
import tempfile
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
os.environ.setdefault("WEBHOOK_SECRET", "test-secret")
# The tests never write to the real bot log
os.environ["LOG_FILE"] = os.path.join(tempfile.mkdtemp(prefix="caccometro_tests_"), "caccometro.log")

from caccometro import database  # noqa: E402
from caccometro import charts  # noqa: E402
from caccometro import webhook  # noqa: E402
from caccometro import i18n  # noqa: E402
from caccometro import maps  # noqa: E402
from caccometro.model import User  # noqa: E402

REAL_CACHED_TILE = maps._cached_tile  # replaced by no_network in every test

CHAT_ID = -1001
BOT_USER = {"id": 7, "is_bot": True, "first_name": "Caccometro", "username": "caccometro_test_bot"}   # what Telegram answers to getMe


@pytest.fixture
def chat_id():
    """The chat ID the tests use.

    Returns:
        int: CHAT_ID.
    """
    return CHAT_ID


@pytest.fixture(autouse=True)
def isolated_folders(tmp_path, monkeypatch):
    """The databases go to a temporary folder, never to the real one.

    Also resets what a test could leak into the next one: the update IDs already seen, the language and the map cache.

    Args:
        tmp_path (pathlib.Path): pytest's temporary folder.
        monkeypatch (pytest.MonkeyPatch): pytest's fixture.

    Returns:
        pathlib.Path: the temporary folder.
    """
    db_dir = tmp_path / "db"
    monkeypatch.setattr(database, "DB_FOLDER", str(db_dir))
    database.init_database(CHAT_ID)
    webhook.SEEN_UPDATE_IDS.clear()   # every test starts like a fresh process
    i18n.use(i18n.DEFAULT_LANGUAGE)   # a test that sets the language outside asyncio.run must not leak it
    monkeypatch.setattr(maps, "CACHE_DIR", tmp_path / "tiles")
    monkeypatch.setattr(maps, "_cached_tile", no_network)  # the tests never fetch map tiles: replies go out as text
    return tmp_path


def no_network(*args):
    """Stand in for the download of a map tile: the tests never fetch map tiles, so replies go out as text.

    Args:
        *args: what _cached_tile would be given.

    Raises:
        OSError: always.
    """
    raise OSError("no network in the tests")


def uid(name):
    """Stable fake Telegram user ID for a test user name.

    Args:
        name (str): the user name.

    Returns:
        int: the ID.
    """
    return zlib.crc32(name.encode("utf-8"))


@pytest.fixture
def seed(chat_id):
    """A function that registers users and their counts: seed({'mario': {'2024-01-01': 1, ...}, ...}).

    A user with no days (e.g. 'luigi': {}) is registered without counts.

    Args:
        chat_id (int): the Telegram chat of the test.

    Returns:
        callable: the function that takes {name: {'YYYY-MM-DD': count}}.
    """
    def _seed(data):
        for name, days in data.items():
            database.upsert_user(chat_id, uid(name), name, name.capitalize())
            for date, count in days.items():
                database.add_count(uid(name), date, count, chat_id)
    return _seed


def get_user(chat_id, user_id):
    """The stored user with this Telegram ID (the bot itself never needs this lookup).

    Args:
        chat_id (int): the Telegram chat.
        user_id (int): the user.

    Returns:
        User: the user, or None.
    """
    conn = database._connect(chat_id)
    try:
        row = conn.execute('SELECT user_id, username, display_name FROM users WHERE user_id = ?', (user_id,)).fetchone()
    finally:
        conn.close()
    return User(*row) if row else None


def make_tg_user(username="mario", user_id=None, full_name=None, is_bot=False):
    """Fake telegram.User.

    Args:
        username (str): the username, or None.
        user_id (int): the ID; None for one made from the name.
        full_name (str): the full name; None for the capitalized username.
        is_bot (bool): True for a bot.

    Returns:
        types.SimpleNamespace: the user.
    """
    if user_id is None:
        user_id = uid(username or full_name or "anonimo")
    if full_name is None:
        full_name = username.capitalize() if username else "Utente"
    return SimpleNamespace(id=user_id, username=username, full_name=full_name,
                           first_name=full_name.split()[0], is_bot=is_bot)


def make_update(text=None, username="mario", user_id=None, chat_id=CHAT_ID,
                sticker_emoji=None, has_from_user=True, full_name=None,
                reply_to=None, is_bot=False, chat_type="group", date=None, reply_in_topic=False, location=None):
    """Fake Telegram Update, enough for the bot handlers.

    Args:
        text (str): the text of the message.
        username (str): the username of the sender.
        user_id (int): the ID of the sender; None for one made from the username.
        chat_id (int): the chat.
        sticker_emoji (str): the emoji of a sticker message.
        has_from_user (bool): False for a message without a sender.
        full_name (str): the full name of the sender.
        reply_to: a make_tg_user(...) of the author of the message being replied to.
        is_bot (bool): True when the sender is a bot.
        chat_type (str): 'group' or 'private'.
        date (datetime): when the message was sent.
        reply_in_topic (bool): the replied message is the one that created a forum topic.
        location (telegram.Location): the location of a location message.

    Returns:
        types.SimpleNamespace: the update.
    """
    chat = SimpleNamespace(type=chat_type, effective_name="Gruppo test")
    from_user = (make_tg_user(username, user_id, full_name, is_bot) if has_from_user else None)
    message = SimpleNamespace(
        text=text,
        date=date,
        from_user=from_user,
        chat_id=chat_id,
        chat=chat,
        sticker=SimpleNamespace(emoji=sticker_emoji) if sticker_emoji else None,
        location=SimpleNamespace(latitude=location[0], longitude=location[1]) if location else None,
        reply_to_message=(SimpleNamespace(from_user=reply_to, forum_topic_created=object() if reply_in_topic else None)
                          if reply_to is not None else None),
        reply_text=AsyncMock(),
        reply_photo=AsyncMock(),
        reply_media_group=AsyncMock(),
    )
    return SimpleNamespace(
        message=message,
        update_id=1,
        _effective_message=message,
        effective_message=message,
    )


def run(coro):
    """Run a coroutine to the end and return its result.

    Args:
        coro (coroutine): what to run.

    Returns:
        The value the coroutine returns.
    """
    return asyncio.run(coro)


def make_context(*args, member_status="member"):
    """Fake CallbackContext.

    context.bot.get_chat_member returns a member with `member_status`, set_my_commands records the menus.

    Args:
        *args: the arguments of the command.
        member_status (str): the status of every chat member.

    Returns:
        types.SimpleNamespace: the context.
    """
    bot = SimpleNamespace(get_chat_member=AsyncMock(return_value=SimpleNamespace(status=member_status)),
                          set_my_commands=AsyncMock())
    return SimpleNamespace(args=list(args), bot=bot)


def make_legacy_db(db_folder, chat_id, rows):
    """Create a database exactly as the old (username-keyed) version did.

    The first database call on that chat migrates it.

    Args:
        db_folder (str): the folder of the database files.
        chat_id (int): the Telegram chat.
        rows (list): [(username, 'YYYY-MM-DD', count)].
    """
    os.makedirs(db_folder, exist_ok=True)
    conn = sqlite3.connect(os.path.join(db_folder, f"{chat_id}_bot_data.db"))
    conn.execute('''CREATE TABLE user_count
                    (username TEXT, date TEXT, count INTEGER DEFAULT 0, PRIMARY KEY (username, date))''')
    conn.executemany("INSERT INTO user_count VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()
