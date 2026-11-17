"""A group that becomes a supergroup keeps its history."""
import asyncio
import os
import shutil

from caccometro import database, messages
from conftest import make_context, make_legacy_db, make_update

OLD, NEW = -100, -1001


def seed_counts(chat_id, count=1):
    database.upsert_user(chat_id, 1, "mario", "Mario")
    database.add_count(1, "2024-03-10", count, chat_id)


def migrate(new_chat_id=NEW, old_chat_id=OLD):
    upd = make_update(chat_id=new_chat_id)
    upd.message.migrate_from_chat_id = old_chat_id
    asyncio.run(messages.handle_migration(upd, make_context()))


def migrate_from_the_old_chat(old_chat_id=OLD, new_chat_id=NEW):
    """The twin message, sent in the old chat."""
    upd = make_update(chat_id=old_chat_id)
    upd.message.migrate_from_chat_id = None
    upd.message.migrate_to_chat_id = new_chat_id
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


def test_when_both_have_counts_they_are_added_up():
    """The migration was handled late: the first 💩 of the supergroup already created a database."""
    seed_counts(OLD, 3)
    database.upsert_user(OLD, 2, "luigi", "Luigi")
    database.add_count(2, "2024-03-11", 4, OLD)
    seed_counts(NEW, 5)  # same user, same day
    database.upsert_user(NEW, 1, "mario_new", "Mario N")  # the newer name wins
    migrate()
    assert database.get_count(1, "2024-03-10", NEW) == 8
    assert database.get_count(2, "2024-03-11", NEW) == 4
    assert database.get_users(NEW)[1].username == "mario_new" and 2 in database.get_users(NEW)
    assert not os.path.exists(database._db_path(OLD))
    assert os.path.exists(database._db_path(OLD) + ".merged")  # the original stays as a backup


def test_a_merge_happens_only_once(tmp_path):
    seed_counts(OLD, 3)
    seed_counts(NEW, 5)
    backup = database._db_path(OLD) + ".copy"
    shutil.copy(database._db_path(OLD), backup)
    migrate()
    shutil.copy(backup, database._db_path(OLD))  # the old file is back (it could not be set aside before)
    migrate()
    assert database.get_count(1, "2024-03-10", NEW) == 8


def test_the_legacy_history_of_the_old_database_comes_along(tmp_path):
    make_legacy_db(os.path.dirname(database._db_path(OLD)), OLD, [("luigi", "2024-03-10", 4)])
    seed_counts(NEW, 5)
    migrate()
    assert database.list_legacy_users(NEW) == [("luigi", 4)]
    assert database.get_count(1, "2024-03-10", NEW) == 5


def test_without_an_old_database_nothing_is_created():
    migrate()
    assert not os.path.exists(database._db_path(OLD))


def test_the_twin_message_of_the_old_chat_moves_the_database_too():
    seed_counts(OLD, 3)
    migrate_from_the_old_chat()
    assert database.get_count(1, "2024-03-10", NEW) == 3
    assert not os.path.exists(database._db_path(OLD))
    migrate()  # the first message arrives later: nothing left to move, nothing breaks
    assert database.get_count(1, "2024-03-10", NEW) == 3
