"""Schema versioning and migration of legacy (username-keyed) databases."""
import os
import sqlite3

import pytest

import conftest
import database

LEGACY_CHAT = -2002
LEGACY_ROWS = [
    ("mario", "2024-03-10", 2),
    ("Mario", "2024-03-11", 1),   # same person with a different spelling
    ("luigi", "2024-03-10", 4),
    (None, "2024-03-12", 3),      # row written before missing usernames were handled
]


def db_file(tmp_path, chat_id):
    return str(tmp_path / "db" / f"{chat_id}_bot_data.db")


def make_legacy_db(tmp_path, chat_id=LEGACY_CHAT, rows=LEGACY_ROWS):
    conftest.make_legacy_db(str(tmp_path / "db"), chat_id, rows)


def query(path, sql, params=()):
    conn = sqlite3.connect(path)
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def columns(path, table):
    return [row[1] for row in query(path, f"PRAGMA table_info({table})")]


def forget_schema_check(path):
    """Simulate a new process: the schema check cache is empty again."""
    database._schema_ready.discard(path)


def test_fresh_database_gets_the_current_schema(tmp_path):
    database.init_database(-3003)
    path = db_file(tmp_path, -3003)
    assert query(path, "PRAGMA user_version") == [(database.SCHEMA_VERSION,)]
    assert columns(path, "user_count") == ["user_id", "date", "count"]
    assert columns(path, "users") == ["user_id", "username", "display_name"]
    tables = {row[0] for row in query(path, "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "user_count_legacy" not in tables
    assert not os.path.exists(path + ".v1.bak")


def test_legacy_database_is_migrated_and_legacy_rows_are_kept(tmp_path):
    make_legacy_db(tmp_path)
    database.init_database(LEGACY_CHAT)
    path = db_file(tmp_path, LEGACY_CHAT)
    assert query(path, "PRAGMA user_version") == [(database.SCHEMA_VERSION,)]
    assert columns(path, "user_count") == ["user_id", "date", "count"]
    legacy = query(path, "SELECT username, date, count FROM user_count_legacy ORDER BY username, date")
    assert sorted(legacy, key=repr) == sorted(LEGACY_ROWS, key=repr)
    assert query(path, "SELECT COUNT(*) FROM user_count") == [(0,)]
    assert database.get_rank(LEGACY_CHAT, "year", "2024") == []


def test_backup_of_the_original_database_is_created(tmp_path):
    make_legacy_db(tmp_path)
    database.init_database(LEGACY_CHAT)
    backup = db_file(tmp_path, LEGACY_CHAT) + ".v1.bak"
    assert os.path.exists(backup)
    assert columns(backup, "user_count") == ["username", "date", "count"]
    assert len(query(backup, "SELECT * FROM user_count")) == len(LEGACY_ROWS)


def test_migration_is_idempotent_and_does_not_touch_new_data(tmp_path):
    make_legacy_db(tmp_path)
    database.init_database(LEGACY_CHAT)
    path = db_file(tmp_path, LEGACY_CHAT)
    database.upsert_user(LEGACY_CHAT, 1, "mario", "Mario")
    database.update_count(1, "2024-04-01", 5, LEGACY_CHAT)
    backup_before = os.path.getmtime(path + ".v1.bak")

    forget_schema_check(path)
    database.init_database(LEGACY_CHAT)

    assert query(path, "SELECT user_id, date, count FROM user_count") == [(1, "2024-04-01", 5)]
    assert len(query(path, "SELECT * FROM user_count_legacy")) == len(LEGACY_ROWS)
    assert os.path.getmtime(path + ".v1.bak") == backup_before


def test_first_use_through_the_normal_api_migrates_too(tmp_path):
    """No explicit init: any call on a legacy database triggers the migration."""
    make_legacy_db(tmp_path)
    assert database.get_count(1, "2024-03-10", LEGACY_CHAT) == 0
    assert query(db_file(tmp_path, LEGACY_CHAT), "PRAGMA user_version") == [(database.SCHEMA_VERSION,)]


def test_failed_migration_rolls_back_completely(tmp_path):
    make_legacy_db(tmp_path)
    path = db_file(tmp_path, LEGACY_CHAT)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE idx_user_count_date (x)")  # makes CREATE INDEX fail halfway through
    conn.commit()
    conn.close()

    with pytest.raises(sqlite3.OperationalError):
        database.init_database(LEGACY_CHAT)

    assert query(path, "PRAGMA user_version") == [(0,)]
    assert columns(path, "user_count") == ["username", "date", "count"]  # not renamed
    assert len(query(path, "SELECT * FROM user_count")) == len(LEGACY_ROWS)
    tables = {row[0] for row in query(path, "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "users" not in tables and "user_count_legacy" not in tables


def test_new_schema_enforces_one_row_per_user_and_day(tmp_path):
    database.init_database(-3003)
    path = db_file(tmp_path, -3003)
    conn = sqlite3.connect(path)
    conn.execute("INSERT INTO user_count VALUES (1, '2024-03-10', 1)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO user_count VALUES (1, '2024-03-10', 2)")
    conn.close()
