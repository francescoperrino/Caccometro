"""Conquest game (#156): the window after the 💩, ownership of the tiles, the king of the hill, /conquests."""
import asyncio
import sqlite3
from datetime import datetime, timedelta, timezone

from caccometro import commands, conquest, database, messages
from conftest import make_context, make_update, uid

MILAN, ROME = (45.4642, 9.19), (41.9028, 12.4964)
T0 = datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc)


def send(name, text=None, location=None, at=T0, chat_type="group"):
    """A message of `name` handled by the bot; returns the reply text."""
    upd = make_update(text=text, username=name, user_id=uid(name), location=location, date=at, chat_type=chat_type)
    asyncio.run(messages.handle_message(upd, make_context()))
    return upd.message.reply_text.call_args.args[0]


def poop_and_conquer(name, location, at=T0):
    send(name, "💩", at=at)
    return send(name, location=location, at=at + timedelta(minutes=1))


# holdings: pure rules

def test_the_last_conqueror_owns_the_tile():
    counts, king = conquest.holdings([(1, "a"), (2, "a"), (1, "b")])
    assert counts == {1: 1, 2: 1} and king == 2  # 2 took the crown with the steal and keeps it on the tie


def test_on_a_tie_the_current_king_keeps_the_crown():
    assert conquest.holdings([(1, "a"), (2, "b")])[1] == 1
    assert conquest.holdings([(1, "a"), (2, "b"), (2, "c")])[1] == 2


def test_the_king_losing_a_tile_passes_the_crown_to_whoever_holds_most():
    # 1 and 2 tie on 2 (1 is king), then 3 steals from 1: 2 holds most
    history = [(1, "a"), (1, "b"), (2, "c"), (2, "d"), (3, "a")]
    counts, king = conquest.holdings(history)
    assert counts == {1: 1, 2: 2, 3: 1} and king == 2


def test_defending_changes_nothing_and_a_member_with_no_tiles_is_dropped():
    assert conquest.holdings([(1, "a"), (1, "a")]) == ({1: 1}, 1)
    assert conquest.holdings([(1, "a"), (2, "a")]) == ({2: 1}, 2)
    assert conquest.visited([(1, "a"), (2, "a"), (1, "b"), (1, "a")], 1) == 2


def test_cells_are_resolution_6():
    import h3
    assert h3.get_resolution(conquest.cell_of(*MILAN)) == 7
    assert conquest.cell_of(*MILAN) != conquest.cell_of(*ROME)


# the window

def test_a_location_without_a_poop_conquers_nothing(chat_id):
    assert send("mario", location=MILAN) == "Prima la 💩, poi la conquista 😏"
    assert database.get_conquests(chat_id) == []


def test_a_location_within_15_minutes_conquers_once(chat_id):
    send("mario", "💩")
    assert send("mario", location=MILAN, at=T0 + timedelta(minutes=15)).startswith("🚩")
    assert send("mario", location=ROME, at=T0 + timedelta(minutes=16)) == "Prima la 💩, poi la conquista 😏"
    assert len(database.get_conquests(chat_id)) == 1


def test_the_window_closes_after_15_minutes_and_does_not_go_backwards(chat_id):
    send("mario", "💩")
    assert send("mario", location=MILAN, at=T0 + timedelta(minutes=15, seconds=1)) == "Prima la 💩, poi la conquista 😏"
    assert send("mario", location=MILAN, at=T0 - timedelta(seconds=1)) == "Prima la 💩, poi la conquista 😏"


def test_add_poop_does_not_open_the_window(chat_id):
    asyncio.run(commands.add_poop_command(make_update(username="mario", user_id=uid("mario")), make_context("oggi")))
    assert send("mario", location=MILAN) == "Prima la 💩, poi la conquista 😏"


def test_the_window_is_per_user_and_per_chat(chat_id):
    send("mario", "💩")
    assert send("luigi", location=MILAN, at=T0 + timedelta(minutes=1)) == "Prima la 💩, poi la conquista 😏"
    upd = make_update(username="mario", user_id=uid("mario"), location=MILAN, date=T0, chat_id=-777)
    asyncio.run(messages.handle_message(upd, make_context()))
    assert upd.message.reply_text.call_args.args[0] == "Prima la 💩, poi la conquista 😏"


# replies

def test_new_stolen_and_defended_tiles_and_the_king(chat_id):
    first = poop_and_conquer("mario", MILAN)
    assert first == "🚩 @mario conquista una nuova zona! Zone: 1\n👑 @mario è il nuovo re della collina!"
    assert poop_and_conquer("mario", MILAN, T0 + timedelta(hours=1)) == "🏠 @mario difende la sua zona. Zone: 1"
    assert poop_and_conquer("luigi", ROME, T0 + timedelta(hours=2)) == "🚩 @luigi conquista una nuova zona! Zone: 1"
    stolen = poop_and_conquer("luigi", MILAN, T0 + timedelta(hours=3))
    assert stolen == "⚔️ @luigi ruba una zona a @mario! Zone: 2\n👑 @luigi è il nuovo re della collina!"
    row = sqlite3.connect(database._db_path(chat_id)).execute("SELECT lat, lon FROM conquests LIMIT 1").fetchone()
    assert row == MILAN


def test_conquests_command(chat_id, monkeypatch):
    monkeypatch.setattr(commands, "now_rome", lambda: datetime(2026, 11, 20, 12))
    poop_and_conquer("mario", MILAN)
    poop_and_conquer("luigi", ROME, T0 + timedelta(hours=1))
    upd = make_update(username="mario", user_id=uid("mario"))
    asyncio.run(commands.conquests_command(upd, make_context()))
    assert upd.message.reply_text.call_args.args[0] == (
        "🗺️ *Conquiste*\n\n🥇 *@mario 👑*: 1 🚩\n🥈 *@luigi*: 1 🚩\n"
        "\n🚩 Stagione ottobre–dicembre 2026: conquistatore *@mario* e *@luigi* (1), re *@mario*")
    upd = make_update(username="luigi", user_id=uid("luigi"))
    asyncio.run(commands.conquests_command(upd, make_context("io")))
    assert upd.message.reply_text.call_args.args[0] == "🗺️ @luigi: 1 zone tenute, 1 visitate."


def test_conquests_command_without_conquests(chat_id):
    upd = make_update()
    asyncio.run(commands.conquests_command(upd, make_context()))
    assert upd.message.reply_text.call_args.args[0].startswith("Nessuna zona conquistata.")


# storage

def test_a_version_2_database_gets_the_conquest_tables(tmp_path):
    path = str(tmp_path / "db" / "-4004_bot_data.db")
    conn = sqlite3.connect(path)
    conn.executescript("""CREATE TABLE users (user_id INTEGER PRIMARY KEY, username TEXT, display_name TEXT NOT NULL);
                          CREATE TABLE user_count (user_id INTEGER NOT NULL, date TEXT NOT NULL,
                                                   count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, date)) WITHOUT ROWID;
                          INSERT INTO user_count VALUES (1, '2026-11-01', 2);
                          PRAGMA user_version = 2;""")
    conn.close()
    assert database.get_count(1, "2026-11-01", -4004) == 2
    assert database.get_conquests(-4004) == []
    assert sqlite3.connect(path).execute("PRAGMA user_version").fetchone()[0] == database.SCHEMA_VERSION


def test_a_version_3_database_gets_its_conquests_recalculated_at_the_new_resolution(tmp_path):
    import h3
    path = str(tmp_path / "db" / "-4005_bot_data.db")
    database._connect(-4005).close()  # current schema, then turned back into a version 3 one with resolution 6 tiles
    database._schema_ready.clear()
    conn = sqlite3.connect(path)
    rows = [(1, 100, *MILAN), (2, 200, *ROME), (3, 300, 45.4780, 9.23)]
    conn.executemany("INSERT INTO conquests VALUES (?, ?, ?, ?, ?)",
                     [(u, ts, h3.latlng_to_cell(lat, lon, 6), lat, lon) for u, ts, lat, lon in rows])
    conn.execute("PRAGMA user_version = 3")
    conn.commit()
    conn.close()
    assert database.get_conquests(-4005) == [(u, conquest.cell_of(lat, lon)) for u, _, lat, lon in rows]  # same order
    assert {h3.get_resolution(cell) for _, cell in database.get_conquests(-4005)} == {conquest.RESOLUTION}
    assert sqlite3.connect(path).execute("PRAGMA user_version").fetchone()[0] == database.SCHEMA_VERSION


def test_a_supergroup_merge_keeps_the_conquests():
    old, new = -100, -1001
    database.upsert_user(old, 1, "mario", "Mario")
    database.add_count(1, "2026-11-01", 1, old)
    database.open_conquest_window(1, 100, old)
    database.conquer(old, 1, 200, 45.0, 9.0, "c1", conquest.WINDOW_SECONDS)
    database.open_conquest_window(1, 300, old)  # window still open when the group is upgraded
    database.add_count(1, "2026-11-02", 1, new)
    assert database.migrate_chat(old, new) == "merged"
    assert database.get_conquests(new) == [(1, "c1")]
    assert database.conquer(new, 1, 400, 45.0, 9.0, "c2", conquest.WINDOW_SECONDS) is not None
