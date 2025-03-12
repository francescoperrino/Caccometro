import os
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import calendar

# Configurations
STORING_FORMAT = "%Y-%m-%d"  # Format used for storing dates in the database
DISPLAY_FORMAT = "%d-%m-%Y"  # Format used for displaying dates in messages
DB_FOLDER = 'db'
CHARTS_FOLDER = 'charts'

# Function to initialize the database
def init_database(chat_id):
    """Initialize the SQLite database if it doesn't exist."""
    # Check if the database folder exists, if not, create it
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)
    # Connect to the database file, creating it if it doesn't exist
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    # Create the user_count table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS user_count
                 (username TEXT,
                 date TEXT,
                 count INTEGER DEFAULT 0,
                 PRIMARY KEY (username, date))''')
    conn.commit()
    conn.close()

# Function to get the count of poop emojis for a given user and date
def get_count(username, date, chat_id):
    """Get the count of poop emojis for a given user and date."""
    # Connect to the database
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    
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
                conn.close()
                return 0
    
    # Execute SQL query to retrieve the count for the specified user and date or month
    c.execute('SELECT SUM(count) FROM user_count WHERE username = ? AND date BETWEEN ? AND ?', (username, start_date, end_date))
    row = c.fetchone()
    conn.close()
    
    # Return the count if found, otherwise return 0
    if row[0] is not None:
        return row[0]
    else:
        return 0

# Function to update the count of poop emojis for a given user and date
def update_count(username, date, count, chat_id):
    """Update the count of poop emojis for a given user and date."""
    # Connect to the database
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    # Delete existing count for the specified user and date
    c.execute('DELETE FROM user_count WHERE username = ? AND date = ?', (username, date))
    # If the count is greater than 0, insert the new count
    if count > 0:
        c.execute('INSERT INTO user_count (username, date, count) VALUES (?, ?, ?)', (username, date, count))
    conn.commit()
    conn.close()

# Function to get the rank of users based on the count of poop emojis
def get_rank(chat_id, time_period, date):
    """Get the rank of users based on the count of poop emojis for the specified time period."""
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

    # Connect to the database
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()

    # Execute SQL query to get the rank based on the time_period
    c.execute('''SELECT username, SUM(count) AS partial_count
              FROM user_count
              WHERE date BETWEEN ? AND ?
              GROUP BY username
              ORDER BY partial_count DESC''', (start_period, end_period))
    
    rows = c.fetchall()
    conn.close()
    return rows

# Function to get statistics of users based on the count of poop emojis
def get_statistics(chat_id, time_period, date):
    """Get the statistics of users based on the count of poop emojis for the specified time period."""
    current_month = datetime.now().month
    current_year = datetime.now().year
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
        month = int(date_parts[0])
        year = int(date_parts[1])
        _, days = calendar.monthrange(year, month)  # Number of days in the month
        current_days = datetime.now().day
    elif time_period == 'year':
        # Parse the input date for yearly rank (format: year)
        start_period = datetime.strptime(f'01-01-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
        end_period = datetime.strptime(f'31-12-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
        year = int(date)
        days = 365 if calendar.isleap(int(date)) else 366  # Number of days in a year
        current_days = (datetime.now() - datetime(current_year, 1, 1)).days + 1
    else:
        raise ValueError("Invalid time_period. It should be 'month' or 'year'.")

    # Connect to the database
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()

    # Get the dates in the period
    date_list = []
    start_date = datetime.strptime(start_period, STORING_FORMAT)
    end_date = datetime.strptime(end_period, STORING_FORMAT)
    delta = timedelta(days=1)
    while start_date <= end_date:
        date_list.append(start_date.strftime(STORING_FORMAT))
        start_date += delta

    # Get the counts for each user for each day in the period
    user_daily_counts = {}
    for date_str in date_list:
        c.execute('''SELECT username, count FROM user_count WHERE date = ?''', (date_str,))
        rows = c.fetchall()
        for username, count in rows:
            if username not in user_daily_counts:
                user_daily_counts[username] = []
            user_daily_counts[username].append(count)

    conn.close()

    # Calculate statistics for each user
    user_statistics = []
    for username, counts in user_daily_counts.items():
        if time_period == 'month':
            expected_days = calendar.monthrange(year, month)[1]
        else:
            expected_days = 366 if calendar.isleap(year) else 365

        if time_period == 'month' and year == current_year and month == current_month:
            valid_days = current_days
        elif time_period == 'year' and year == current_year:
            valid_days = (datetime.now() - datetime(current_year, 1, 1)).days + 1
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
            'username': username,
            'mean': mean,
            'median': median,
            'variance': variance
        })

    # Sort user_statistics by mean in descending order and variance in ascending order
    sorted_user_statistics = sorted(user_statistics, key=lambda x: (-x['mean'], x['variance']))

    return sorted_user_statistics

# Function to get the records for the specific user
def get_record(username, chat_id):
    """Get the records for the specific user."""
    # Connect to the database
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()

    # Execute SQL query to get the records for the specific user
    c.execute('''SELECT date, count
              FROM user_count
              WHERE username = ?
              ORDER BY date''', (username,))

    rows = c.fetchall()
    conn.close()

    return rows

# Function to get constipation days for the specific user
def get_constipation_days(username, chat_id):
    """Get the constipation days for the specific user."""
    # Connect to the database
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()

    # Execute SQL query to get the constipation days for the specific user
    c.execute('''SELECT date
                 FROM user_count
                 WHERE username = ? AND count > 0
                 ORDER BY date DESC
                 LIMIT 1''', (username,))
    
    last_day = c.fetchone()
    conn.close()
    
    if last_day:
        last_day = datetime.strptime(last_day[0], "%Y-%m-%d").date()
        today = datetime.today().date()
        
        return (today - last_day).days
    
    return None