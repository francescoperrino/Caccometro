import os
import calendar
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import matplotlib.colors as mcolors
from database import now_rome, STORING_FORMAT, CHARTS_FOLDER
import locale
from math import ceil, floor, log10
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

# Set the locale to Italian
locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')

# Check if charts folder exists, if not, create it
os.makedirs(CHARTS_FOLDER, exist_ok=True)

def normal_pdf(x, mean, std):
    """Probability density of a normal distribution (same values as scipy.stats.norm.pdf, without scipy)."""
    z = (np.asarray(x, dtype=float) - mean) / std
    return np.exp(-0.5 * z * z) / (std * np.sqrt(2 * np.pi))

def chart_label(name):
    """Make a user name safe for matplotlib text ('$' would start a math expression)."""
    return name.replace('$', r'\$')

def generate_rank_chart(rank, daily_counts, chat_id, time_period, date):
    """
    Generates the monthly ranking table and chart.

    Args:
        rank (list): List of tuples containing a database.User and its count.
        daily_counts (dict): {user_id: {'YYYY-MM-DD': count}} for the period (see database.get_daily_counts).
        chat_id (int): ID of the chat.
        time_period (str): Time period ('month' or 'year').
        date (str): Date in 'month-year' or 'year' format.

    Returns:
        None
    """
    if time_period == 'month':
        # Parse the input date for monthly rank (format: month-year)
        date_parts = date.split('-')
        month = int(date_parts[0])
        year = int(date_parts[1])
        _, days = calendar.monthrange(year, month)
        period_label = calendar.month_name[month] + ' ' + str(year)
        saving_date = str(date_parts[1]) + '_' + str(date_parts[0])
        steps = days
        x_labels = [str(day) for day in range(1, days + 1)]  # Labels for each day of the month

    elif time_period == 'year':
        # Parse the input date for yearly rank (format: year)
        year = int(date)
        days = 366 if calendar.isleap(year) else 365  # Number of days in a year
        steps = 12  # Number of months in a year
        period_label = str(year)
        saving_date = date
        x_labels = [calendar.month_abbr[count_month] for count_month in range(1, steps + 1)]  # Labels for each month of the year

    # Create the figure with two subplots
    fig, axes = plt.subplots(2, 1, figsize=(15, 12))

    # Generate the table
    names = {user.user_id: chart_label(user.name) for user, _ in rank}
    # Sort users (by ID) alphabetically by name
    users = sorted(names, key=lambda user_id: (names[user_id].lower(), user_id))
    axes[1].set_xticklabels([])
    if time_period == 'month':
        table_data = [[''] + [f'{step}' for step in range(1, steps + 1)] + ['Total']]  # Set days when time_period is 'month'
    elif time_period == 'year':
        table_data = [[''] + [f'{calendar.month_abbr[count_month]}' for count_month in range(1, steps + 1)] + ['Total']]  # Set months when time_period is 'year'

    max_total = 0  # Variable to store the maximum total count for highlighting

    for user in users:
        row = [names[user]]
        total_count = 0
        user_days = daily_counts.get(user, {})
        if time_period == 'year':
            # Monthly totals from the daily counts ('YYYY-MM-DD' -> month at positions 5:7)
            month_totals = defaultdict(int)
            for day_str, day_count in user_days.items():
                month_totals[int(day_str[5:7])] += day_count
        for step in range(1, steps + 1):
            if time_period == 'month':
                count = user_days.get(f'{year}-{month:02}-{step:02}', 0)  # Count for the specific day
            elif time_period == 'year':
                count = month_totals.get(step, 0)  # Count for the specific month
            total_count += count
            row.append(count)
        row.append(total_count)  # Add total count for the period
        table_data.append(row)

        # Update max_total if necessary
        max_total = max(max_total, total_count)

    # Draw the table
    table = axes[0].table(cellText=table_data, loc='center', colWidths=[0.1] + [0.03] * steps + [0.05],  
                          cellLoc='center', fontsize=8)

    for key, cell in table.get_celld().items():
        cell.set_edgecolor('black')  # Set edge color for each cell
        cell.set_linewidth(1)  # Set linewidth for each cell

    table.auto_set_font_size(True)
    table.set_fontsize(8)

    # Set title for the table (month name and year)
    axes[0].set_title(f'{period_label.capitalize()}', fontsize=14)

    # Hide the axes for the table
    axes[0].axis('off')

    # Highlight cell with highest total count in brown color
    for i, row in enumerate(table_data):
        for j, value in enumerate(row):
            if value == max_total and j == len(row) - 1:  # Check if it's the last cell (total column)
                table.get_celld()[(i, j)].set_facecolor('#D2B48C')  # Set brown color for total column

    # Generate the chart
    for user in users:
        user_days = daily_counts.get(user, {})
        cumulative_counts = []
        cumulative_count = 0
        for day in range(1, days + 1):
            if time_period == 'month':
                count_date = f'{year}-{month:02}-{day:02}'
            elif time_period == 'year':
                doy = datetime.strptime(f'{year}-{day}', '%Y-%j')
                count_date = doy.strftime(STORING_FORMAT)
            count = user_days.get(count_date, 0)  # Count for each day in month or year
            cumulative_count += count
            cumulative_counts.append(cumulative_count)

        axes[1].plot(range(1, days + 1), cumulative_counts, label=names[user])

    # Set legend for the chart below the chart
    axes[1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=len(users), fontsize=8)

    # Set labels on x-axis
    if time_period == 'month':
        axes[1].set_xticks(range(1, days + 1))
        axes[1].set_xticklabels(x_labels)  # Set x-axis labels based on time_period
    elif time_period == 'year':
        # Find the start day of each month in the year
        start_days = [1]  # Start with the first day of January
        for month in range(1, 12):  # Loop through the months
            _, days_in_month = calendar.monthrange(year, month)
            start_days.append(start_days[-1] + days_in_month)  # Add the start day of the next month
        # Set the ticks at the start of each month
        axes[1].set_xticks(start_days)
        axes[1].set_xticklabels(x_labels)  # Set x-axis labels based on time_period

    # Set y-axis range from 0 to the next multiple of 10 after max_total
    max_y = max(10, ceil(max_total / 10) * 10)  # at least 10: avoids log10(0) when there are no counts
    order_of_magnitude = 10 ** floor(log10(max_y))

    tick_interval = order_of_magnitude / 2 if max_y / order_of_magnitude <= 5 else order_of_magnitude
    
    axes[1].set_yticks(np.arange(0, max_y + tick_interval, tick_interval))
    axes[1].set_ylim(0, max_y)

    # Add horizontal lines every count
    if tick_interval == order_of_magnitude / 2:
        for count in np.arange(0, max_y + tick_interval / 5, tick_interval / 5):
            axes[1].axhline(y=count, color='#DDDDDD', linestyle='--', linewidth=0.3)
        for count in np.arange(0, max_y + tick_interval / 2, tick_interval / 2):
            axes[1].axhline(y=count, color='#CCCCCC', linestyle='--', linewidth=0.7)
        for count in np.arange(0, max_y + tick_interval, tick_interval):
            axes[1].axhline(y=count, color='#888888', linestyle='--', linewidth=1)
    else:
        for count in np.arange(0, max_y + tick_interval / 10, tick_interval / 10):
            axes[1].axhline(y=count, color='#DDDDDD', linestyle='--', linewidth=0.3)
        for count in np.arange(0, max_y + tick_interval / 5, tick_interval / 5):
            axes[1].axhline(y=count, color='#CCCCCC', linestyle='--', linewidth=0.7)
        for count in np.arange(0, max_y + tick_interval, tick_interval):
            axes[1].axhline(y=count, color='#888888', linestyle='--', linewidth=1)

    # Add vertical lines
    if time_period == 'month':
        for day in range(1, days + 1):
            axes[1].axvline(x=day, color='#DDDDDD', linestyle='--', linewidth=0.3)
    elif time_period == 'year':
        # Find the start day of each month in the year and add vertical lines at those points
        start_days = [1]  # Start with the first day of January
        for month in range(1, 12):  # Loop through the months
            _, days_in_month = calendar.monthrange(year, month)
            start_days.append(start_days[-1] + days_in_month)  # Add the start day of the next month
        for start_day in start_days:
            axes[1].axvline(x=start_day, color='#DDDDDD', linestyle='--', linewidth=0.3)

    # Set x-axis limits to include only the actual days of the month
    axes[1].set_xlim(left=1, right=days)

    # Adjust layout to prevent overlapping titles
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save the figure to an image file
    plt.savefig(os.path.join(CHARTS_FOLDER, f'{chat_id}_{saving_date}_chart.png'), bbox_inches='tight')

    # Close figure
    plt.close(fig)

def generate_statistics_chart(statistics, daily_counts, chat_id, time_period, date):
    """
    Generates charts (histogram and box plot) for monthly and yearly statistics in a single plot,
    with added Gaussian fitting to the histogram.

    Args:
        statistics (list): List of dictionaries containing user statistics.
        daily_counts (dict): {user_id: {'YYYY-MM-DD': count}} for the period (see database.get_daily_counts).
        chat_id (int): ID of the chat.
        time_period (str): Time period ('month' or 'year').
        date (str): Date in 'month-year' or 'year' format.

    Returns:
        None
    """
    names = {stat['user'].user_id: chart_label(stat['user'].name) for stat in statistics}
    users_stats = sorted([(stat['user'].user_id, stat['mean'], stat['variance']) for stat in statistics],
                         key=lambda item: (names[item[0]].lower(), item[0]))
    users, means, variances = zip(*users_stats)
    counts = []

    today = now_rome()

    if time_period == 'month':
        date_parts = date.split('-')
        month = int(date_parts[0])
        year = int(date_parts[1])
        _, days = calendar.monthrange(year, month)
        period_label = calendar.month_name[month] + ' ' + str(year)
        saving_date = str(date_parts[1]) + '_' + str(date_parts[0])
        end_date = datetime(year, month, days)
        if year == today.year and month == today.month:
            end_date = today
    elif time_period == 'year':
        year = int(date)
        period_label = str(year)
        saving_date = date
        end_date = datetime(year, 12, 31)
        if year == today.year:
            end_date = today

    # Daily counts of every user, from the first day of the period to the last valid day
    user_daily_counts = {}
    for user in users:
        user_days = daily_counts.get(user, {})
        user_daily_counts[user] = []
        current_date = datetime(year, 1, 1) if time_period == 'year' else datetime(year, month, 1)
        delta = timedelta(days=1)
        while current_date <= end_date:
            user_daily_counts[user].append(user_days.get(current_date.strftime(STORING_FORMAT), 0))
            current_date += delta

    # How many days each user had each count (for the distribution curves)
    user_occurrence_counts = {}
    max_occurrence = 0
    for user in users:
        user_occurrence_counts[user] = {}
        for count in user_daily_counts[user]:
            user_occurrence_counts[user][count] = user_occurrence_counts[user].get(count, 0) + 1
            max_occurrence = max(max_occurrence, count)

    fig, axes = plt.subplots(2, 1, figsize=(15, 12))

    occurrence_values = range(max(max_occurrence, 1) + 1)  # at least 0..1: avoids a zero-width x axis
    bar_width = 1
    max_y = 0

    # Gaussian fitting in axes[0]
    for i, user in enumerate(users):
        counts = [user_occurrence_counts[user].get(val, 0) for val in occurrence_values]
        mean = means[i]
        std = np.sqrt(variances[i]) if variances[i] > 0 else 0
        if std > 0:
            x = np.linspace(min(occurrence_values), max(occurrence_values), 100)
            p = normal_pdf(x, mean, std)
            axes[0].plot(x, p * sum(counts) * bar_width, '-', label=names[user])
            axes[0].fill_between(x, p * sum(counts) * bar_width, alpha=0.3)

            # Add vertical line at the mean
            gaussian_value_at_mean = normal_pdf(mean, mean, std) * sum(counts) * bar_width
            axes[0].vlines(mean, 0, gaussian_value_at_mean, linestyles='--', colors=f'C{i}', linewidth=2)

    axes[0].grid(axis='y', linestyle='--', alpha=0.7)

    # Calculate max height of gaussian curves
    max_gaussian_height = 0
    for i, user in enumerate(users):
        counts = [user_occurrence_counts[user].get(val, 0) for val in occurrence_values]
        mean = means[i]
        std = np.sqrt(variances[i]) if variances[i] > 0 else 0
        if std > 0:
            x = np.linspace(min(occurrence_values), max(occurrence_values), 100)
            p = normal_pdf(x, mean, std)
            max_gaussian_height = max(max_gaussian_height, max(p * sum(counts) * bar_width))

    # Calculate max y value for the plot
    if max_gaussian_height > 0:
        max_y = ceil(max_gaussian_height / 5) * 5
    else:
        max_y = 5  # no drawable curve (zero variance): minimum scale, avoids log10(0)
    order_of_magnitude = 10 ** floor(log10(max_y))

    tick_interval = order_of_magnitude / 2 if max_y / order_of_magnitude <= 5 else order_of_magnitude

    axes[0].set_yticks(np.arange(0, max_y + tick_interval, tick_interval))
    axes[0].set_ylim(0, max_y)

    # Adapt hline to order of magnitude
    if tick_interval == order_of_magnitude / 2:
        for count in np.arange(0, max_y + tick_interval / 5, tick_interval / 5):
            axes[0].axhline(y=count, color='#DDDDDD', linestyle='--', linewidth=0.3)
        for count in np.arange(0, max_y + tick_interval / 2, tick_interval / 2):
            axes[0].axhline(y=count, color='#CCCCCC', linestyle='--', linewidth=0.7)
        for count in np.arange(0, max_y + tick_interval, tick_interval):
            axes[0].axhline(y=count, color='#888888', linestyle='--', linewidth=1)
    else:
        for count in np.arange(0, max_y + tick_interval / 10, tick_interval / 10):
            axes[0].axhline(y=count, color='#DDDDDD', linestyle='--', linewidth=0.3)
        for count in np.arange(0, max_y + tick_interval / 5, tick_interval / 5):
            axes[0].axhline(y=count, color='#CCCCCC', linestyle='--', linewidth=0.7)
        for count in np.arange(0, max_y + tick_interval, tick_interval):
            axes[0].axhline(y=count, color='#888888', linestyle='--', linewidth=1)

    axes[0].set_xlim(min(occurrence_values), max(occurrence_values))

    # Add mean values as x-axis ticks
    xticks = sorted(list(set(list(occurrence_values) + list(means))))
    axes[0].set_xticks(xticks)

    tick_labels = []
    for tick in xticks:
        if tick in means:
            tick_labels.append(f'{tick:.2f}')
        else:
            tick_labels.append(str(int(tick)))

    axes[0].set_xticklabels(tick_labels, rotation=0, ha='center')

    # Set colors and font sizes for mean ticks
    for tick in xticks:
        if tick in means:
            i = means.index(tick)
            for text in axes[0].get_xticklabels():
                if text.get_text() == f'{tick:.2f}':
                    text.set_color(f'C{i}')
                    text.set_fontsize(6)

    axes[0].set_title(f'{period_label.capitalize()}', fontsize=14)
    if axes[0].get_legend_handles_labels()[0]:  # no legend when there are no curves
        axes[0].legend(loc='upper right')

    # Box plot in axes[1]
    max_user_daily_counts = max(max(user_daily_counts[user]) for user in users if user_daily_counts[user])

    box_plot = axes[1].boxplot(list(user_daily_counts.values()), labels=[names[user] for user in users], patch_artist=True, sym='x')

    for i, (user, patch) in enumerate(zip(users, box_plot['boxes'])):
        color = f'C{i}'
        rgba_color = mcolors.to_rgba(color)
        patch.set_facecolor((rgba_color[0], rgba_color[1], rgba_color[2], 0.5))
        patch.set_edgecolor(color)
        patch.set_linewidth(1.5)

        box_plot['whiskers'][i * 2].set_color(color)
        box_plot['whiskers'][i * 2 + 1].set_color(color)

        box_plot['caps'][i*2].set_color(color)
        box_plot['caps'][i*2+1].set_color(color)

        box_plot['fliers'][i].set_markeredgecolor(color)
        box_plot['fliers'][i].set_markerfacecolor(color)
    
    for median in box_plot['medians']:
        median.set(color='black', linewidth=1.5)

    axes[1].grid(axis='y', linestyle='--', alpha=0.7)
    axes[1].set_yticks(np.arange(0, max_user_daily_counts + 2, 1))
    axes[1].set_ylim(0, max_user_daily_counts + 1)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    plt.savefig(os.path.join(CHARTS_FOLDER, f'{chat_id}_{saving_date}_stats.png'), bbox_inches='tight')
    plt.close(fig)
