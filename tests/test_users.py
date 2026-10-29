"""The users table: current username and display name of every user the bot has seen."""
import database
from database import User


def test_user_name_and_mention():
    with_username = User(1, "mario", "Mario Rossi")
    without_username = User(2, None, "Anna Bianchi")
    assert (with_username.name, with_username.mention) == ("mario", "@mario")
    assert (without_username.name, without_username.mention) == ("Anna Bianchi", "Anna Bianchi")


def test_upsert_user_inserts_and_get_user_finds_it(chat_id):
    database.upsert_user(chat_id, 10, "mario", "Mario Rossi")
    assert database.get_user(chat_id, 10) == User(10, "mario", "Mario Rossi")
    assert database.get_user(chat_id, 11) is None


def test_upsert_user_updates_username_and_name(chat_id):
    database.upsert_user(chat_id, 10, "mario", "Mario Rossi")
    database.upsert_user(chat_id, 10, "mario_new", "Mario R.")
    assert database.get_user(chat_id, 10) == User(10, "mario_new", "Mario R.")
    assert database.find_user_by_username(chat_id, "mario") is None


def test_upsert_user_can_drop_the_username(chat_id):
    database.upsert_user(chat_id, 10, "mario", "Mario Rossi")
    database.upsert_user(chat_id, 10, None, "Mario Rossi")
    assert database.get_user(chat_id, 10) == User(10, None, "Mario Rossi")


def test_find_user_by_username_is_case_insensitive(chat_id):
    database.upsert_user(chat_id, 10, "Mario_Rossi", "Mario")
    assert database.find_user_by_username(chat_id, "mario_rossi").user_id == 10
    assert database.find_user_by_username(chat_id, "MARIO_ROSSI").user_id == 10


def test_a_reassigned_username_moves_to_the_new_holder(chat_id):
    database.upsert_user(chat_id, 10, "mario", "Mario Rossi")
    database.upsert_user(chat_id, 20, "Mario", "Another Mario")  # the old holder changed username elsewhere
    assert database.find_user_by_username(chat_id, "mario").user_id == 20
    assert database.get_user(chat_id, 10) == User(10, None, "Mario Rossi")


def test_upsert_without_changes_does_not_write(chat_id, monkeypatch):
    database.upsert_user(chat_id, 10, "mario", "Mario Rossi")
    statements = []
    real_connect = database._connect

    def traced_connect(chat):
        conn = real_connect(chat)
        conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(database, "_connect", traced_connect)
    database.upsert_user(chat_id, 10, "mario", "Mario Rossi")
    assert statements, "the user should have been read"
    assert not [sql for sql in statements if sql.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))]
