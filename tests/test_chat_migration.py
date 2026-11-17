"""A group that becomes a supergroup keeps its history."""
import asyncio
import os

from caccometro import database, messages
from conftest import make_context, make_update

OLD, NEW = -100, -1001


def seed_counts(chat_id, count=1):
    database.upsert_user(chat_id, 1, "mario", "Mario")
    database.add_count(1, "2024-03-10", count, chat_id)


def migrate(new_chat_id=NEW, old_chat_id=OLD):
    upd = make_update(chat_id=new_chat_id)
    upd.message.migrate_from_chat_id = old_chat_id
    asyncio.run(messages.handle_migration(upd, make_context()))


def test_the_old_database_becomes_the_new_one():
    seed_counts(OLD, 3)
    migrate()
    assert database.get_count(1, "2024-03-10", NEW) == 3
    assert not os.path.exists(database._db_path(OLD))


def test_an_empty_new_database_is_replaced():
    seed_counts(OLD, 3)
    database.init_database(NEW)  # a message of the new chat arrived first
    migrate()
    assert database.get_count(1, "2024-03-10", NEW) == 3


def test_when_both_have_counts_nothing_changes():
    seed_counts(OLD, 3)
    seed_counts(NEW, 5)
    migrate()
    assert database.get_count(1, "2024-03-10", OLD) == 3
    assert database.get_count(1, "2024-03-10", NEW) == 5


def test_without_an_old_database_nothing_is_created():
    migrate()
    assert not os.path.exists(database._db_path(OLD))


def test_the_message_of_the_old_chat_is_ignored():
    seed_counts(OLD, 3)
    migrate(new_chat_id=OLD, old_chat_id=None)
    assert database.get_count(1, "2024-03-10", OLD) == 3
