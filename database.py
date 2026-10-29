import os
import sqlite3
from datetime import datetime
from typing import NamedTuple, Optional
import numpy as np
import calendar
import pytz

# Configurations
STORING_FORMAT = "%Y-%m-%d"  # Format used for storing dates in the database
DISPLAY_FORMAT = "%d-%m-%Y"  # Format used for displaying dates in messages
DB_FOLDER = 'db'
CHARTS_FOLDER = 'charts'
ROME_TZ = pytz.timezone('Europe/Rome')

# Schema versions (stored in PRAGMA user_version):
#   0/1 = legacy: counts keyed by Telegram username
#   2   = counts keyed by Telegram user ID, plus a users table
SCHEMA_VERSION = 2

def now_rome():
    """Current date/time in Rome, without tzinfo (comparable with the naive datetimes used in the code).

    The server runs in UTC: datetime.now() would return the wrong day
    between 22:00/23:00 and midnight in Italy.
    """
    return datetime.now(ROME_TZ).replace(tzinfo=None)


class User(NamedTuple):
    """A Telegram user known to a chat."""
    user_id: int
    username: Optional[str]
    display_name: str

    @property
    def name(self):
        """Plain name for charts and tables: the username if any, otherwise the display name."""
        return self.username or self.display_name

    @property
    def mention(self):
        """Name for messages: '@username' if any, otherwise the display name."""
        return f"@{self.username}" if self.username else self.display_name


# Database files whose schema has already been checked by this process
_schema_ready = set()

def _db_path(chat_id):
    return os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db')

def _connect(chat_id):
    """Open the database of a chat, creating or migrating its schema on first use."""
    path = _db_path(chat_id)
    if path not in _schema_ready:
        _ensure_schema(path)
        _schema_ready.add(path)
    return sqlite3.connect(path, timeout=30)

def _has_legacy_table(conn):
    """True if user_count still has the legacy layout (rows keyed by username)."""
    columns = [row[1] for row in conn.execute("PRAGMA table_info(user_count)")]
    return 'username' in columns

def _has_table(conn, name):
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone()
    return row is not None

def _backup_legacy_database(conn, path):
    """Keep a copy of the database as it was before the migration (only the first time)."""
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
                conn.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
    finally:
        conn.close()

# Function to initialize the database
def init_database(chat_id):
    """Initialize (or migrate) the SQLite database of a chat if needed."""
    _connect(chat_id).close()


# Users

def _to_user(user_id, username, display_name):
    return User(user_id, username, display_name or str(user_id))

def upsert_user(chat_id, user_id, username, display_name):
    """Record the current username and display name of a user (writes only when something changed)."""
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
    """Find a known user by (case-insensitive) username; None if the bot has never seen it."""
    conn = _connect(chat_id)
    try:
        row = conn.execute('SELECT user_id, username, display_name FROM users WHERE username = ? COLLATE NOCASE LIMIT 1',
                           (username,)).fetchone()
    finally:
        conn.close()
    return _to_user(*row) if row else None

def get_user(chat_id, user_id):
    """Find a known user by Telegram user ID."""
    conn = _connect(chat_id)
    try:
        row = conn.execute('SELECT user_id, username, display_name FROM users WHERE user_id = ?', (user_id,)).fetchone()
    finally:
        conn.close()
    return _to_user(*row) if row else None


# Counts

# Function to get the count of poop emojis for a given user and date
def get_count(user_id, date, chat_id):
    """Get the count of poop emojis for a given user ID and date."""
    # Determine if the input date is a day, a month, or invalid
    try:
        parsed_date = datetime.strptime(date, STORING_FORMAT)
        start_date = parsed_date.strftime(STORING_FORMAT)
        end_date = parsed_date.strftime(STORING_FORMAT)
    except ValueError:
        try:
            parsed_date = datetime.strptime(date, '%Y-%m')
            year = parsed_date.year
            month = parsed_date.month
            _, days_in_month = calendar.monthrange(year, month)
            start_date = parsed_date.strftime('%Y-%m-01')
            end_date = parsed_date.strftime(f'%Y-%m-{days_in_month}')
        except ValueError:
            try:
                parsed_date = datetime.strptime(date, '%d-%m-%Y')
                start_date = parsed_date.strftime(STORING_FORMAT)
                end_date = parsed_date.strftime(STORING_FORMAT)
            except ValueError:
                return 0

    conn = _connect(chat_id)
    try:
        # Execute SQL query to retrieve the count for the specified user and date or month
        row = conn.execute('SELECT SUM(count) FROM user_count WHERE user_id = ? AND date BETWEEN ? AND ?',
                           (user_id, start_date, end_date)).fetchone()
    finally:
        conn.close()

    # Return the count if found, otherwise return 0
    return row[0] if row[0] is not None else 0

# Function to update the count of poop emojis for a given user and date
def update_count(user_id, date, count, chat_id):
    """Set the count of poop emojis for a given user ID and date (a count of 0 removes the row)."""
    conn = _connect(chat_id)
    try:
        if count > 0:
            conn.execute('''INSERT INTO user_count (user_id, date, count) VALUES (?, ?, ?)
                            ON CONFLICT(user_id, date) DO UPDATE SET count = excluded.count''',
                         (user_id, date, count))
        else:
            conn.execute('DELETE FROM user_count WHERE user_id = ? AND date = ?', (user_id, date))
        conn.commit()
    finally:
        conn.close()

def add_count(user_id, date, delta, chat_id):
    """Add delta (e.g. +1 or -1) to the count of a user on a day, in a single transaction.

    Reading and writing happen under the same write lock, so concurrent updates cannot overwrite
    each other. The count never goes below 0 (a count of 0 removes the row).
    Returns (old_count, new_count).
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
    """{user_id: {'YYYY-MM-DD': count}} for every day with at least one 💩 in the period (one query)."""
    daily = {}
    for user_id, day, count in conn.execute('SELECT user_id, date, count FROM user_count WHERE date BETWEEN ? AND ?',
                                            (start_period, end_period)):
        daily.setdefault(user_id, {})[day] = count
    return daily

def get_daily_counts(chat_id, time_period, date):
    """Counts of every user for every day of a period ('month' + 'MM-YYYY', or 'year' + 'YYYY').

    One query for the whole period. Returns {user_id: {'YYYY-MM-DD': count}}; days without 💩 are absent.
    """
    start_period, end_period = _period_bounds(time_period, date)
    conn = _connect(chat_id)
    try:
        return _daily_counts(conn, start_period, end_period)
    finally:
        conn.close()

def _period_bounds(time_period, date):
    """Start and end date (storing format) of a month ('MM-YYYY') or year ('YYYY')."""
    if time_period == 'month':
        # Parse the input date for monthly rank (format: month-year)
        date_parts = date.split('-')
        month_str = date_parts[0].zfill(2)  # Add leading zero, if necessary
        year_str = date_parts[1]
        start_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y').strftime(STORING_FORMAT)
        # Get the end of the month
        end_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y')\
                        .replace(day=calendar.monthrange(int(year_str), int(month_str))[1])\
                        .strftime(STORING_FORMAT)
    elif time_period == 'year':
        # Parse the input date for yearly rank (format: year)
        start_period = datetime.strptime(f'01-01-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
        end_period = datetime.strptime(f'31-12-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
    else:
        raise ValueError("Invalid time_period. It should be 'month' or 'year'.")
    return start_period, end_period

# Function to get the rank of users based on the count of poop emojis
def get_rank(chat_id, time_period, date):
    """Get the rank of users for the specified period, as a list of (User, count) sorted by count."""
    start_period, end_period = _period_bounds(time_period, date)

    conn = _connect(chat_id)
    try:
        # Execute SQL query to get the rank based on the time_period
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

# Function to get statistics of users based on the count of poop emojis
def get_statistics(chat_id, time_period, date):
    """Get the statistics of users for the specified period, as a list of dicts with a 'user' (User) key."""
    now = now_rome()
    current_month = now.month
    current_year = now.year
    start_period, end_period = _period_bounds(time_period, date)
    if time_period == 'month':
        date_parts = date.split('-')
        month = int(date_parts[0])
        year = int(date_parts[1])
        _, days = calendar.monthrange(year, month)  # Number of days in the month
        current_days = now.day
    else:
        year = int(date)
        days = 366 if calendar.isleap(int(date)) else 365  # Number of days in a year
        current_days = (now - datetime(current_year, 1, 1)).days + 1

    conn = _connect(chat_id)
    try:
        # Counts of every user for the whole period, with a single query
        user_daily_counts = _daily_counts(conn, start_period, end_period)

        users = {user_id: _to_user(user_id, username, display_name)
                 for user_id, username, display_name in conn.execute('SELECT user_id, username, display_name FROM users')}
    finally:
        conn.close()

    # Calculate statistics for each user
    user_statistics = []
    for user_id, per_day in user_daily_counts.items():
        counts = [per_day[day] for day in sorted(per_day)]
        if time_period == 'month':
            expected_days = calendar.monthrange(year, month)[1]
        else:
            expected_days = 366 if calendar.isleap(year) else 365

        if time_period == 'month' and year == current_year and month == current_month:
            valid_days = current_days
        elif time_period == 'year' and year == current_year:
            valid_days = (now - datetime(current_year, 1, 1)).days + 1
        else:
            valid_days = expected_days

        if len(counts) < valid_days:
            counts += [0] * (valid_days - len(counts))
        elif len(counts) > valid_days:
            counts = counts[:valid_days]

        if counts:
            mean = round(sum(counts) / valid_days, 2)
            median = np.median(counts)
            variance = round(sum((x - mean) ** 2 for x in counts) / valid_days, 2)
        else:
            median = mean = variance = 0  # If there's not enough data, set default values

        user_statistics.append({
            'user': users.get(user_id) or _to_user(user_id, None, None),
            'mean': mean,
            'median': median,
            'variance': variance
        })

    # Sort user_statistics by mean in descending order and variance in ascending order
    sorted_user_statistics = sorted(user_statistics, key=lambda x: (-x['mean'], x['variance']))

    return sorted_user_statistics

# Function to get the records for the specific user
def get_record(user_id, chat_id):
    """Get the (date, count) records of a user, sorted by date."""
    conn = _connect(chat_id)
    try:
        return conn.execute('''SELECT date, count
                               FROM user_count
                               WHERE user_id = ?
                               ORDER BY date''', (user_id,)).fetchall()
    finally:
        conn.close()

# Function to get constipation days for the specific user
def get_constipation_days(user_id, chat_id):
    """Get the constipation days for the specific user."""
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


# Legacy data (counts recorded by username before the user-ID schema)

def list_legacy_users(chat_id):
    """Legacy usernames not yet linked to a user, as [(username, total_count)] sorted by name.

    Usernames that differ only by case are grouped; rows without a username are not listed.
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
    """Number of legacy rows without a username: they cannot be linked to anybody by name."""
    conn = _connect(chat_id)
    try:
        if not _has_table(conn, 'user_count_legacy'):
            return 0
        return conn.execute('SELECT COUNT(*) FROM user_count_legacy WHERE username IS NULL').fetchone()[0]
    finally:
        conn.close()

def link_legacy_username(chat_id, legacy_username, user_id):
    """Move the legacy history of a username (case-insensitive) to a user ID.

    Counts of the same day are summed with the ones the user already has. Returns the number
    of days moved (0 if there is nothing to link, e.g. already linked).
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

    Returns [(legacy_username, User, days_moved)] for the links that were made.
    """
    linked = []
    for legacy_username, _ in list_legacy_users(chat_id):
        user = find_user_by_username(chat_id, legacy_username)
        if user is not None:
            linked.append((legacy_username, user, link_legacy_username(chat_id, legacy_username, user.user_id)))
    return linked
