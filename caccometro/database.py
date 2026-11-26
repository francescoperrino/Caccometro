"""SQLite storage, one database file per chat: schema, migration from the legacy schema, counts, users and conquests.

Every public function opens the database of the chat it is given, creating or migrating it on first use.
"""

import os
import sqlite3
from datetime import datetime

import h3

from caccometro.config import PROJECT_DIR, now_rome, period_bounds
from caccometro.model import User

# One database file per chat lives in this folder
DB_FOLDER = str(PROJECT_DIR / 'db')

# Schema versions (stored in PRAGMA user_version):
#   0/1 = legacy: counts keyed by Telegram username
#   2   = counts keyed by Telegram user ID, plus a users table
#   3   = conquest game: conquests and last_poop tables (#156)
#   4   = conquest tiles at h3 resolution 7: every saved conquest recalculated from its location (#174)
SCHEMA_VERSION = 4
SCHEMA_4_RESOLUTION = 7   # frozen: a later change of conquest.RESOLUTION needs a schema 5

# Database files whose schema has already been checked by this process
_schema_ready = set()

def _db_path(chat_id):
    """Path of the database file of a chat.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        str: the file inside DB_FOLDER.
    """
    return os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db')

def _connect(chat_id):
    """Open the database of a chat, creating or migrating its schema on first use.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        sqlite3.Connection: a connection the caller must close.
    """
    path = _db_path(chat_id)
    if path not in _schema_ready:
        _ensure_schema(path)
        _schema_ready.add(path)
    return sqlite3.connect(path, timeout=30)

def _has_legacy_table(conn):
    """Tell whether user_count still has the legacy layout (rows keyed by username).

    Args:
        conn (sqlite3.Connection): an open connection.

    Returns:
        bool: True for the legacy layout.
    """
    columns = [row[1] for row in conn.execute("PRAGMA table_info(user_count)")]
    return 'username' in columns

def _has_table(conn, name):
    """Tell whether the database has a table.

    Args:
        conn (sqlite3.Connection): an open connection.
        name (str): the table name.

    Returns:
        bool: True if the table exists.
    """
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone()
    return row is not None

def _backup_legacy_database(conn, path):
    """Keep a copy of the database as it was before the migration (only the first time).

    Args:
        conn (sqlite3.Connection): a connection to the database to copy.
        path (str): the database file; the copy is `<path>.v1.bak`.
    """
    backup_path = path + '.v1.bak'
    if os.path.exists(backup_path):
        return
    backup = sqlite3.connect(backup_path)
    try:
        conn.backup(backup)
    finally:
        backup.close()

def _ensure_schema(path):
    """Create the schema if missing, or migrate a legacy database to the user-ID schema.

    The migration runs in a single transaction. The legacy rows are kept untouched in the
    user_count_legacy table: they are linked to user IDs later, on explicit request.

    Args:
        path (str): the database file; its folder is created if missing.
    """
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None, timeout=30)  # manual transaction control
    try:
        if conn.execute('PRAGMA user_version').fetchone()[0] >= SCHEMA_VERSION:
            return
        if _has_legacy_table(conn):
            _backup_legacy_database(conn, path)
        conn.execute('BEGIN IMMEDIATE')
        try:
            # Another worker may have migrated the database while we were waiting for the lock
            if conn.execute('PRAGMA user_version').fetchone()[0] < SCHEMA_VERSION:
                if _has_legacy_table(conn):
                    conn.execute('ALTER TABLE user_count RENAME TO user_count_legacy')
                conn.execute('''CREATE TABLE IF NOT EXISTS users
                                (user_id INTEGER PRIMARY KEY,
                                 username TEXT,
                                 display_name TEXT NOT NULL)''')
                conn.execute('''CREATE TABLE IF NOT EXISTS user_count
                                (user_id INTEGER NOT NULL,
                                 date TEXT NOT NULL,
                                 count INTEGER NOT NULL DEFAULT 0,
                                 PRIMARY KEY (user_id, date)) WITHOUT ROWID''')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_user_count_date ON user_count (date)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username COLLATE NOCASE)')
                # Every conquest is kept: the owner of a tile is its latest row (the order the bot handled them)
                conn.execute('''CREATE TABLE IF NOT EXISTS conquests
                                (user_id INTEGER NOT NULL,
                                 ts INTEGER NOT NULL,
                                 cell TEXT NOT NULL,
                                 lat REAL NOT NULL,
                                 lon REAL NOT NULL)''')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_conquests_cell ON conquests (cell)')
                # Time of the last 💩 of each user while its conquest window is unused
                conn.execute('CREATE TABLE IF NOT EXISTS last_poop (user_id INTEGER PRIMARY KEY, ts INTEGER NOT NULL)')
                # The tile of every conquest again from its location, at the resolution of schema 4 (rows keep their order)
                conn.create_function('cell_of', 2, lambda lat, lon: h3.latlng_to_cell(lat, lon, SCHEMA_4_RESOLUTION),
                                     deterministic=True)
                conn.execute('UPDATE conquests SET cell = cell_of(lat, lon)')
                conn.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
    finally:
        conn.close()

def _merge_into(old_chat_id, new_chat_id):
    """Add the users and counts of the old database to the new one, in one transaction (same user and day: summed).

    A marker row in the new database makes it happen once even if the old file could not be set aside afterwards.

    Args:
        old_chat_id (int): the chat that was upgraded.
        new_chat_id (int): the supergroup that replaces it.

    Returns:
        int: the number of count rows added, or None if the legacy history of both databases would collide.
    """
    old_path = _db_path(old_chat_id)
    _connect(old_chat_id).close()  # a legacy layout is migrated first
    conn = _connect(new_chat_id)
    conn.isolation_level = None  # ATTACH cannot run inside a transaction
    try:
        conn.execute('ATTACH DATABASE ? AS old', (old_path,))
        legacy_sql = conn.execute("SELECT sql FROM old.sqlite_master WHERE type = 'table' AND name = 'user_count_legacy'").fetchone()
        if legacy_sql and _has_table(conn, 'user_count_legacy'):
            return None
        conn.execute('BEGIN IMMEDIATE')
        try:
            conn.execute('CREATE TABLE IF NOT EXISTS merged_chats (chat_id INTEGER PRIMARY KEY)')
            if conn.execute('SELECT 1 FROM merged_chats WHERE chat_id = ?', (old_chat_id,)).fetchone():
                added = 0  # merged before
            else:
                conn.execute('INSERT OR IGNORE INTO users SELECT user_id, username, display_name FROM old.users')  # the new row wins
                added = conn.execute('''INSERT INTO user_count (user_id, date, count)
                                        SELECT user_id, date, count FROM old.user_count WHERE true
                                        ON CONFLICT(user_id, date) DO UPDATE SET count = count + excluded.count''').rowcount
                # shortcut: the old conquests go after the new ones, so they win a tile both hold; the gap is minutes
                conn.execute('INSERT INTO conquests SELECT * FROM old.conquests ORDER BY rowid')
                conn.execute('''INSERT INTO last_poop SELECT user_id, ts FROM old.last_poop WHERE true
                                ON CONFLICT(user_id) DO UPDATE SET ts = MAX(ts, excluded.ts)''')
                if legacy_sql:
                    conn.execute(legacy_sql[0])
                    conn.execute('INSERT INTO user_count_legacy SELECT * FROM old.user_count_legacy')
                conn.execute('INSERT INTO merged_chats VALUES (?)', (old_chat_id,))
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        return added
    finally:
        conn.close()

def migrate_chat(old_chat_id, new_chat_id):
    """Move the database of a group that became a supergroup to its new chat ID.

    A database of the new ID that holds no counts yet (created by a message that arrived first) is replaced.
    When it already holds counts (the migration was handled late) the old database is added to it, and kept
    as <old>.merged.

    Args:
        old_chat_id (int): the chat that was upgraded.
        new_chat_id (int): the supergroup that replaces it.

    Returns:
        str: 'moved', 'merged', 'no_old' (nothing to move) or 'both_have_data' (nothing changed).
    """
    old_path, new_path = _db_path(old_chat_id), _db_path(new_chat_id)
    if not os.path.exists(old_path):
        return 'no_old'
    if os.path.exists(new_path):
        conn = _connect(new_chat_id)
        try:
            has_counts = conn.execute('SELECT EXISTS (SELECT 1 FROM user_count)').fetchone()[0]
        finally:
            conn.close()
        if has_counts:
            if _merge_into(old_chat_id, new_chat_id) is None:
                return 'both_have_data'
            os.replace(old_path, old_path + '.merged')
            _schema_ready.discard(old_path)
            return 'merged'
    os.replace(old_path, new_path)
    _schema_ready.discard(old_path)
    _schema_ready.discard(new_path)
    return 'moved'

def init_database(chat_id):
    """Initialize (or migrate) the SQLite database of a chat if needed.

    Args:
        chat_id (int): the Telegram chat.
    """
    _connect(chat_id).close()


# Settings

def get_language(chat_id):
    """Language chosen for the chat with /language.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        str: the language code, or None when it was never chosen.
    """
    conn = _connect(chat_id)
    try:
        if not _has_table(conn, 'settings'):
            return None
        row = conn.execute("SELECT value FROM settings WHERE key = 'language'").fetchone()
    finally:
        conn.close()
    return row[0] if row else None

def set_language(chat_id, language):
    """Store the language of the chat (the settings table is created by the first choice).

    Args:
        chat_id (int): the Telegram chat.
        language (str): the language code.
    """
    conn = _connect(chat_id)
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        conn.execute("""INSERT INTO settings (key, value) VALUES ('language', ?)
                        ON CONFLICT(key) DO UPDATE SET value = excluded.value""", (language,))
        conn.commit()
    finally:
        conn.close()


# Users

def _to_user(user_id, username, display_name):
    """Build a User from a users row; the user ID stands in for a missing display name.

    Args:
        user_id (int): Telegram ID.
        username (str): the username, or None.
        display_name (str): the name shown in Telegram, or None.

    Returns:
        User: the user.
    """
    return User(user_id, username, display_name or str(user_id))

def _users(conn):
    """All known users of the chat.

    Args:
        conn (sqlite3.Connection): an open connection.

    Returns:
        dict: {user_id: User}.
    """
    return {user_id: _to_user(user_id, username, display_name)
            for user_id, username, display_name in conn.execute('SELECT user_id, username, display_name FROM users')}

def get_users(chat_id):
    """Every user known to the chat.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        dict: {user_id: User}.
    """
    conn = _connect(chat_id)
    try:
        return _users(conn)
    finally:
        conn.close()

def upsert_user(chat_id, user_id, username, display_name):
    """Record the current username and display name of a user (writes only when something changed).

    A username belongs to one account at a time: it is released from any previous holder.

    Args:
        chat_id (int): the Telegram chat.
        user_id (int): Telegram ID.
        username (str): the username, or None.
        display_name (str): the name shown in Telegram.
    """
    conn = _connect(chat_id)
    try:
        row = conn.execute('SELECT username, display_name FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if row == (username, display_name):
            return
        if username:
            # A username belongs to one account at a time: release it from any previous holder
            conn.execute('UPDATE users SET username = NULL WHERE username = ? COLLATE NOCASE AND user_id != ?',
                         (username, user_id))
        conn.execute('''INSERT INTO users (user_id, username, display_name) VALUES (?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            username = excluded.username,
                            display_name = excluded.display_name''',
                     (user_id, username, display_name))
        conn.commit()
    finally:
        conn.close()

def find_user_by_username(chat_id, username):
    """Find a known user by username, ignoring the case.

    Args:
        chat_id (int): the Telegram chat.
        username (str): the username without the @.

    Returns:
        User: the user, or None if the bot has never seen that username.
    """
    conn = _connect(chat_id)
    try:
        row = conn.execute('SELECT user_id, username, display_name FROM users WHERE username = ? COLLATE NOCASE LIMIT 1',
                           (username,)).fetchone()
    finally:
        conn.close()
    return _to_user(*row) if row else None


# Counts

def get_count(user_id, date, chat_id):
    """Count of 💩 of a user on a day.

    Args:
        user_id (int): Telegram ID.
        date (str): the day as 'YYYY-MM-DD'.
        chat_id (int): the Telegram chat.

    Returns:
        int: the count, 0 if none.
    """
    conn = _connect(chat_id)
    try:
        row = conn.execute('SELECT count FROM user_count WHERE user_id = ? AND date = ?', (user_id, date)).fetchone()
    finally:
        conn.close()
    return row[0] if row else 0

def add_count(user_id, date, delta, chat_id):
    """Add a change to the count of a user on a day, in a single transaction.

    Reading and writing happen under the same write lock, so concurrent updates cannot overwrite
    each other. The count never goes below 0 (a count of 0 removes the row).

    Args:
        user_id (int): Telegram ID.
        date (str): the day as 'YYYY-MM-DD'.
        delta (int): the change, e.g. +1 or -1.
        chat_id (int): the Telegram chat.

    Returns:
        (old_count, new_count): the counts before and after the change.
    """
    conn = _connect(chat_id)
    conn.isolation_level = None  # manual transaction control
    try:
        conn.execute('BEGIN IMMEDIATE')
        try:
            row = conn.execute('SELECT count FROM user_count WHERE user_id = ? AND date = ?', (user_id, date)).fetchone()
            old_count = row[0] if row else 0
            new_count = max(old_count + delta, 0)
            if new_count > 0:
                conn.execute('''INSERT INTO user_count (user_id, date, count) VALUES (?, ?, ?)
                                ON CONFLICT(user_id, date) DO UPDATE SET count = excluded.count''',
                             (user_id, date, new_count))
            elif row:
                conn.execute('DELETE FROM user_count WHERE user_id = ? AND date = ?', (user_id, date))
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        return old_count, new_count
    finally:
        conn.close()

def _daily_counts(conn, start_period, end_period):
    """Counts of every day with at least one 💩 in a period, with one query.

    Args:
        conn (sqlite3.Connection): an open connection.
        start_period (str): first day, 'YYYY-MM-DD'.
        end_period (str): last day, 'YYYY-MM-DD'.

    Returns:
        dict: {user_id: {'YYYY-MM-DD': count}}.
    """
    daily = {}
    for user_id, day, count in conn.execute('SELECT user_id, date, count FROM user_count WHERE date BETWEEN ? AND ?',
                                            (start_period, end_period)):
        daily.setdefault(user_id, {})[day] = count
    return daily

def get_daily_counts(chat_id, time_period, date):
    """Counts of every user for every day of a month or a year.

    Args:
        chat_id (int): the Telegram chat.
        time_period (str): 'month' or 'year'.
        date (str): 'MM-YYYY' for a month, 'YYYY' for a year.

    Returns:
        dict: {user_id: {'YYYY-MM-DD': count}}; days without 💩 are absent.
    """
    return get_daily_counts_between(chat_id, *period_bounds(time_period, date))

def get_daily_counts_between(chat_id, start_period, end_period):
    """Like get_daily_counts, for any range of days.

    Args:
        chat_id (int): the Telegram chat.
        start_period (str): first day, 'YYYY-MM-DD'.
        end_period (str): last day, 'YYYY-MM-DD', included.

    Returns:
        dict: {user_id: {'YYYY-MM-DD': count}}; days without 💩 are absent.
    """
    conn = _connect(chat_id)
    try:
        return _daily_counts(conn, start_period, end_period)
    finally:
        conn.close()

def get_rank(chat_id, time_period, date):
    """Total 💩 of every user in a month or a year, best first.

    Args:
        chat_id (int): the Telegram chat.
        time_period (str): 'month' or 'year'.
        date (str): 'MM-YYYY' for a month, 'YYYY' for a year.

    Returns:
        list: [(User, total)] sorted by total, then by name.
    """
    start_period, end_period = period_bounds(time_period, date)

    conn = _connect(chat_id)
    try:
        rows = conn.execute('''SELECT c.user_id, u.username, u.display_name, SUM(c.count) AS partial_count
                               FROM user_count c
                               LEFT JOIN users u ON u.user_id = c.user_id
                               WHERE c.date BETWEEN ? AND ?
                               GROUP BY c.user_id
                               ORDER BY partial_count DESC, COALESCE(u.username, u.display_name) COLLATE NOCASE''',
                            (start_period, end_period)).fetchall()
    finally:
        conn.close()
    return [(_to_user(user_id, username, display_name), total) for user_id, username, display_name, total in rows]

def get_record(user_id, chat_id):
    """The counts of one user.

    Args:
        user_id (int): Telegram ID.
        chat_id (int): the Telegram chat.

    Returns:
        list: [(date, count)] sorted by date.
    """
    conn = _connect(chat_id)
    try:
        return conn.execute('''SELECT date, count
                               FROM user_count
                               WHERE user_id = ?
                               ORDER BY date''', (user_id,)).fetchall()
    finally:
        conn.close()

def get_all_user_rows(chat_id):
    """The counts of every user of the chat, read with a single query.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        (rows, users): rows is {user_id: [(date, count), ...] sorted by date}, users is {user_id: User}.
    """
    conn = _connect(chat_id)
    try:
        rows = {}
        for user_id, day, count in conn.execute('SELECT user_id, date, count FROM user_count ORDER BY user_id, date'):
            rows.setdefault(user_id, []).append((day, count))
        users = _users(conn)
    finally:
        conn.close()
    return rows, users

def get_days_since_last_poop(user_id, chat_id):
    """Days since the last 💩 of a user.

    Args:
        user_id (int): Telegram ID.
        chat_id (int): the Telegram chat.

    Returns:
        int: 0 for today; None when the user never made any 💩.
    """
    conn = _connect(chat_id)
    try:
        last_day = conn.execute('''SELECT date
                                   FROM user_count
                                   WHERE user_id = ? AND count > 0
                                   ORDER BY date DESC
                                   LIMIT 1''', (user_id,)).fetchone()
    finally:
        conn.close()

    if last_day:
        last_day = datetime.strptime(last_day[0], "%Y-%m-%d").date()
        today = now_rome().date()

        return (today - last_day).days

    return None


# Conquest game

def open_conquest_window(user_id, ts, chat_id):
    """Remember the time of a 💩 of the user: it opens the conquest window.

    Args:
        user_id (int): Telegram ID.
        ts (int): Unix seconds of the 💩.
        chat_id (int): the Telegram chat.
    """
    conn = _connect(chat_id)
    try:
        conn.execute('''INSERT INTO last_poop (user_id, ts) VALUES (?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET ts = MAX(ts, excluded.ts)''', (user_id, ts))
        conn.commit()
    finally:
        conn.close()

def conquer(chat_id, user_id, ts, lat, lon, cell, window):
    """Conquer a tile if the user sent a 💩 shortly before; the window is then used up.

    One transaction, so two locations of the same window cannot both conquer.

    Args:
        chat_id (int): the Telegram chat.
        user_id (int): Telegram ID.
        ts (int): Unix seconds of the location.
        lat (float): latitude of the location.
        lon (float): longitude of the location.
        cell (str): the h3 cell of the location.
        window (int): seconds the window stays open after the 💩.

    Returns:
        (previous_owner, history): previous_owner is None for a new tile; history is every conquest
        [(user_id, cell)] in order, the new one last. None when there is no open window.
    """
    conn = _connect(chat_id)
    conn.isolation_level = None  # manual transaction control
    try:
        conn.execute('BEGIN IMMEDIATE')
        try:
            row = conn.execute('SELECT ts FROM last_poop WHERE user_id = ?', (user_id,)).fetchone()
            if row is None or not 0 <= ts - row[0] <= window:
                conn.execute('COMMIT')
                return None
            conn.execute('DELETE FROM last_poop WHERE user_id = ?', (user_id,))
            owner = conn.execute('SELECT user_id FROM conquests WHERE cell = ? ORDER BY rowid DESC LIMIT 1',
                                 (cell,)).fetchone()
            conn.execute('INSERT INTO conquests (user_id, ts, cell, lat, lon) VALUES (?, ?, ?, ?, ?)',
                         (user_id, ts, cell, lat, lon))
            history = _conquests(conn)
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        return (owner[0] if owner else None), history
    finally:
        conn.close()

def _conquests(conn):
    """Every conquest in the order the bot handled them.

    Args:
        conn (sqlite3.Connection): an open connection.

    Returns:
        list: [(user_id, cell)].
    """
    return conn.execute('SELECT user_id, cell FROM conquests ORDER BY rowid').fetchall()

def get_timed_conquests(chat_id):
    """Every conquest of the chat, with its time, for the seasons.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        list: [(user_id, ts, cell)] in the order they were made.
    """
    conn = _connect(chat_id)
    try:
        return conn.execute('SELECT user_id, ts, cell FROM conquests ORDER BY rowid').fetchall()
    finally:
        conn.close()


# Legacy data (counts recorded by username before the user-ID schema)

def list_legacy_users(chat_id):
    """The legacy usernames not yet linked to a user.

    Usernames that differ only by case are grouped; rows without a username are not listed.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        list: [(username, total_count)] sorted by name.
    """
    conn = _connect(chat_id)
    try:
        if not _has_table(conn, 'user_count_legacy'):
            return []
        return conn.execute('''SELECT MIN(username), SUM(count)
                               FROM user_count_legacy
                               WHERE username IS NOT NULL
                               GROUP BY LOWER(username)
                               ORDER BY LOWER(username)''').fetchall()
    finally:
        conn.close()

def count_legacy_orphans(chat_id):
    """Count the legacy rows without a username: they cannot be linked to anybody by name.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        int: the number of rows.
    """
    conn = _connect(chat_id)
    try:
        if not _has_table(conn, 'user_count_legacy'):
            return 0
        return conn.execute('SELECT COUNT(*) FROM user_count_legacy WHERE username IS NULL').fetchone()[0]
    finally:
        conn.close()

def link_legacy_username(chat_id, legacy_username, user_id):
    """Move the legacy history of a username to a user ID, ignoring the case.

    Counts of the same day are summed with the ones the user already has.

    Args:
        chat_id (int): the Telegram chat.
        legacy_username (str): the old username.
        user_id (int): Telegram ID of the person it belongs to.

    Returns:
        int: the number of days moved, 0 if there is nothing to link (for instance already linked).
    """
    conn = _connect(chat_id)
    conn.isolation_level = None  # manual transaction control
    try:
        if not _has_table(conn, 'user_count_legacy'):
            return 0
        conn.execute('BEGIN IMMEDIATE')
        try:
            rows = conn.execute('''SELECT date, SUM(count)
                                   FROM user_count_legacy
                                   WHERE username = ? COLLATE NOCASE
                                   GROUP BY date''', (legacy_username,)).fetchall()
            for date, count in rows:
                conn.execute('''INSERT INTO user_count (user_id, date, count) VALUES (?, ?, ?)
                                ON CONFLICT(user_id, date) DO UPDATE SET count = count + excluded.count''',
                             (user_id, date, count))
            conn.execute('DELETE FROM user_count_legacy WHERE username = ? COLLATE NOCASE', (legacy_username,))
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        return len(rows)
    finally:
        conn.close()

def link_legacy_by_username(chat_id):
    """Link every legacy username that matches the username of a known user.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        list: [(legacy_username, User, days_moved)] for the links that were made.
    """
    linked = []
    for legacy_username, _ in list_legacy_users(chat_id):
        user = find_user_by_username(chat_id, legacy_username)
        if user is not None:
            linked.append((legacy_username, user, link_legacy_username(chat_id, legacy_username, user.user_id)))
    return linked

def get_first_days(chat_id):
    """The first day with 💩 of every user of the chat.

    Args:
        chat_id (int): the Telegram chat.

    Returns:
        dict: {user_id: 'YYYY-MM-DD'}.
    """
    conn = _connect(chat_id)
    try:
        return dict(conn.execute('SELECT user_id, MIN(date) FROM user_count WHERE count > 0 GROUP BY user_id'))
    finally:
        conn.close()
