"""Linking the old username-based history to Telegram users (database level)."""
import database
from conftest import make_legacy_db

CHAT = -2002
ROWS = [
    ("mario", "2024-03-10", 2),
    ("Mario", "2024-03-11", 1),   # same person, different spelling
    ("luigi", "2024-03-10", 4),
    (None, "2024-03-12", 3),      # no username: cannot be linked by name
]


def legacy_chat(tmp_path, rows=ROWS):
    make_legacy_db(str(tmp_path / "db"), CHAT, rows)
    return CHAT


def test_list_legacy_users_groups_spellings_and_skips_null(tmp_path):
    chat = legacy_chat(tmp_path)
    listed = database.list_legacy_users(chat)
    # one entry per person; which spelling is shown is not important
    assert [(name.lower(), total) for name, total in listed] == [("luigi", 4), ("mario", 3)]
    assert database.count_legacy_orphans(chat) == 1


def test_no_legacy_data_on_a_fresh_database(chat_id):
    assert database.list_legacy_users(chat_id) == []
    assert database.count_legacy_orphans(chat_id) == 0
    assert database.link_legacy_username(chat_id, "mario", 1) == 0
    assert database.link_legacy_by_username(chat_id) == []


def test_link_moves_the_history_to_the_user_id(tmp_path):
    chat = legacy_chat(tmp_path)
    assert database.link_legacy_username(chat, "mario", 42) == 2   # two different days
    assert database.get_record(42, chat) == [("2024-03-10", 2), ("2024-03-11", 1)]
    assert database.list_legacy_users(chat) == [("luigi", 4)]      # mario is gone from the legacy list


def test_link_is_case_insensitive(tmp_path):
    chat = legacy_chat(tmp_path)
    assert database.link_legacy_username(chat, "MARIO", 42) == 2


def test_link_sums_with_counts_the_user_already_has(tmp_path):
    chat = legacy_chat(tmp_path)
    database.update_count(42, "2024-03-10", 5, chat)   # the user wrote after the migration
    database.link_legacy_username(chat, "mario", 42)
    assert database.get_count(42, "2024-03-10", chat) == 7


def test_link_twice_does_nothing_the_second_time(tmp_path):
    chat = legacy_chat(tmp_path)
    database.link_legacy_username(chat, "mario", 42)
    assert database.link_legacy_username(chat, "mario", 99) == 0
    assert database.get_record(99, chat) == []


def test_link_unknown_username_returns_zero(tmp_path):
    chat = legacy_chat(tmp_path)
    assert database.link_legacy_username(chat, "nessuno", 42) == 0
    assert len(database.list_legacy_users(chat)) == 2


def test_link_does_not_touch_other_legacy_users(tmp_path):
    chat = legacy_chat(tmp_path)
    database.link_legacy_username(chat, "mario", 42)
    assert database.list_legacy_users(chat) == [("luigi", 4)]
    assert database.count_legacy_orphans(chat) == 1


def test_linked_history_appears_in_the_ranking(tmp_path):
    chat = legacy_chat(tmp_path)
    database.upsert_user(chat, 42, "mario", "Mario")
    database.link_legacy_username(chat, "mario", 42)
    ((user, count),) = database.get_rank(chat, "year", "2024")
    assert (user.user_id, count) == (42, 3)


def test_link_by_username_links_only_known_users(tmp_path):
    chat = legacy_chat(tmp_path)
    database.upsert_user(chat, 42, "Mario", "Mario Rossi")     # luigi has never written
    linked = database.link_legacy_by_username(chat)
    assert [(name.lower(), user.user_id, days) for name, user, days in linked] == [("mario", 42, 2)]
    assert database.list_legacy_users(chat) == [("luigi", 4)]


def test_link_by_username_is_repeatable(tmp_path):
    chat = legacy_chat(tmp_path)
    database.upsert_user(chat, 42, "mario", "Mario")
    database.link_legacy_by_username(chat)
    database.upsert_user(chat, 43, "luigi", "Luigi")           # luigi writes later
    linked = database.link_legacy_by_username(chat)
    assert [(name, user.user_id) for name, user, _ in linked] == [("luigi", 43)]
    assert database.list_legacy_users(chat) == []
