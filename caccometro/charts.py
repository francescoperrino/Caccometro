"""Charts of /classifica_* and /statistiche_*: one shared style, PNG bytes in memory."""
import io
import calendar
from collections import defaultdict
from datetime import datetime, timedelta
from math import ceil, floor, log10
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import font_manager
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MaxNLocator
import numpy as np

from caccometro.config import MONTH_NAMES, now_rome, STORING_FORMAT

MONTH_ABBRS = ['', 'gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic']

# Colours taken from the bot avatar. The user colours are in a fixed order checked for colour
# blindness on the card colour (8 slots; a 9th user gets a dashed line).
PALETTE = ['#a0561e', '#e0902b', '#2aa3e0', '#4caf50', '#7d5ba6', '#c94f3d', '#2f4f8f', '#e0607e']
BACKGROUND = '#f3e4d0'  # warm tiles behind the cards
SURFACE = '#fffaf3'     # cards
TEXT = '#3b2a1e'
TEXT_MUTED = '#7a6a5c'
GRID = '#eadccb'
HEADER = '#2f4f8f'      # table header, the denim of the avatar
TOTAL = '#f7ecdc'
FUTURE = '#efe6da'      # days still to come

# Emoji drawn as images (matplotlib cannot draw colour emoji as text): Noto Emoji, assets/emoji/LICENSE.txt
EMOJI_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'emoji'
MEDALS = [plt.imread(EMOJI_DIR / f'medal_{n}.png') for n in (1, 2, 3)]  # 🥇 🥈 🥉

# Rounded font (Nunito, SIL Open Font License) shipped in assets/fonts; DejaVu Sans fills the missing glyphs
FONT_FILES = sorted((Path(__file__).resolve().parent.parent / 'assets' / 'fonts').glob('*.ttf'))
for font_file in FONT_FILES:
    font_manager.fontManager.addfont(str(font_file))
FONTS = [font_manager.FontProperties(fname=str(FONT_FILES[0])).get_name()] if FONT_FILES else []

STYLE = {
    'font.family': FONTS + ['DejaVu Sans'],
    'figure.facecolor': BACKGROUND, 'axes.facecolor': SURFACE, 'savefig.facecolor': BACKGROUND,
    'font.size': 13, 'axes.titlesize': 22, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
    'axes.titlepad': 16, 'axes.titlecolor': TEXT, 'axes.labelsize': 13, 'axes.labelcolor': TEXT_MUTED,
    'axes.edgecolor': GRID, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': GRID, 'grid.linewidth': 0.8,
    'xtick.color': TEXT_MUTED, 'ytick.color': TEXT_MUTED, 'xtick.labelsize': 11, 'ytick.labelsize': 12,
    'text.color': TEXT, 'lines.linewidth': 3, 'lines.solid_capstyle': 'round',
    'legend.frameon': True, 'legend.fancybox': True, 'legend.facecolor': SURFACE, 'legend.edgecolor': GRID,
    'legend.framealpha': 0.95, 'legend.fontsize': 13, 'legend.borderpad': 0.7,
}


def png_bytes(fig):
    """Render a figure to PNG in memory and close it."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=110, bbox_inches='tight', pad_inches=0.35)
    plt.close(fig)
    return buffer.getvalue()

def normal_pdf(x, mean, std):
    """Probability density of a normal distribution (same values as scipy.stats.norm.pdf, without scipy)."""
    z = (np.asarray(x, dtype=float) - mean) / std
    return np.exp(-0.5 * z * z) / (std * np.sqrt(2 * np.pi))

def chart_label(name):
    """Make a user name safe for matplotlib text ('$' would start a math expression)."""
    return name.replace('$', r'\$')

NAME_MAX = 16       # characters of a name that fit the name column of the rank table; longer ones are cut


def short_name(name):
    """The name cut to NAME_MAX characters, with an ellipsis when cut."""
    return name if len(name) <= NAME_MAX else name[:NAME_MAX - 1] + '…'

def user_style(i):
    """Colour and line style of the i-th user (users sorted by name, so a user keeps the colour across charts)."""
    return PALETTE[i % len(PALETTE)], '-' if i < len(PALETTE) else '--'

def decimal(value):
    """Italian decimal comma: 1.25 -> '1,25'."""
    return f'{value:.2f}'.replace('.', ',')

def period_info(time_period, date):
    """Year, month (None for a year), number of days and title of the period."""
    if time_period == 'month':
        month, year = (int(part) for part in date.split('-'))
        return year, month, calendar.monthrange(year, month)[1], f'{MONTH_NAMES[month]} {year}'
    year = int(date)
    return year, None, 366 if calendar.isleap(year) else 365, str(year)

def last_day_shown(year, month, days):
    """Days of the period to draw: all of a past period, up to today for the current one."""
    today = now_rome()
    if year == today.year and (month is None or month == today.month):
        return today.timetuple().tm_yday if month is None else today.day
    return days

FINE_GRID = '#f1e8dc'   # thin lines at every unit, behind the main grid


def fine_vlines(ax, xs):
    """Thin vertical grid lines at the x positions `xs`."""
    for x in xs:
        ax.axvline(x, color=FINE_GRID, linewidth=0.6, zorder=0)

def layered_grid(ax, top, round_to, fine_step=None):
    """Y axis from 0 to `top` rounded up to `round_to`: a solid line at every power of ten step
    (10, 20, ... or 100, 200, ...), a dashed one halfway (5, 15, ...) and, with `fine_step`, thin lines in between."""
    max_y = max(round_to, ceil(top / round_to) * round_to)
    order = 10 ** floor(log10(max_y))
    tick = order / 2 if max_y / order <= 5 else order
    ax.grid(False)
    levels = ((order / 2, '--', '#dccbb5', 1.0), (order, '-', '#b8a48c', 1.0))
    if fine_step is not None:
        levels = ((fine_step, '-', FINE_GRID, 0.6),) + levels
    for step, style, colour, width in levels:
        for y in np.arange(0, max_y + step / 2, step):
            ax.axhline(y, color=colour, linestyle=style, linewidth=width, zorder=0)
    ax.set_yticks(np.arange(0, max_y + tick / 2, tick))
    ax.set_ylim(0, max_y)

def add_cards(fig, axes):
    """A rounded card behind every axes, its labels and its title included."""
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_tightbbox(renderer).transformed(fig.transFigure.inverted()) for ax in axes]
    left = min(box.x0 for box in boxes)  # same width for every card
    right = max(box.x1 for box in boxes)
    pad = 0.015
    for box in boxes:
        fig.patches.append(FancyBboxPatch(
            (left - pad, box.y0 - pad), right - left + 2 * pad, box.height + 2 * pad,
            boxstyle='round,pad=0,rounding_size=0.02', transform=fig.transFigure,
            facecolor=SURFACE, edgecolor='none', zorder=-1))

def sorted_by_name(names):
    """User IDs of `names` (user ID -> name) sorted by name, case-insensitive."""
    return sorted(names, key=lambda user_id: (names[user_id].lower(), user_id))

def emoji(ax, image, xy, zoom, coords='axes fraction'):
    """Draw an emoji image centred on xy."""
    ax.add_artist(AnnotationBbox(OffsetImage(image, zoom=zoom), xy, xycoords=coords, frameon=False,
                                 zorder=6, annotation_clip=False))

def positions(rank):
    """Ranking positions with ties (20, 20, 18 -> 1, 1, 3)."""
    result = []
    for i, (_, total) in enumerate(rank):
        result.append(result[-1] if i and total == rank[i - 1][1] else i + 1)
    return result

def generate_rank_chart(rank, daily_counts, time_period, date, forecast=None):
    """
    Ranking chart: a table of the counts per day (month) or per month (year) with the totals and the
    medals, and the cumulative counts of every user below it.

    Args:
        rank (list): (database.User, total) pairs, best first.
        daily_counts (dict): {user_id: {'YYYY-MM-DD': count}} for the period (see database.get_daily_counts).
        time_period (str): 'month' or 'year'.
        date (str): 'MM-YYYY' or 'YYYY'.
        forecast (dict): {user_id: expected total at the end of the period}, drawn as a dotted line from
            today to the last day (see analysis.forecast_totals); None for a past period.

    Returns:
        bytes: the PNG image.
    """
    forecast = forecast or {}
    year, month, days, title = period_info(time_period, date)
    shown = last_day_shown(year, month, days)
    names = {user.user_id: chart_label(user.name) for user, _ in rank}
    colour_order = sorted_by_name(names)  # colours follow the user, not the position in the ranking
    totals = {user.user_id: total for user, total in rank}
    rows = [user.user_id for user, _ in rank]  # table rows in ranking order, leader first
    max_total = max(list(totals.values()) + list(forecast.values()), default=0)

    if time_period == 'month':
        header = [str(day) for day in range(1, days + 1)]
        steps_shown = shown
    else:
        header = MONTH_ABBRS[1:]
        steps_shown = datetime.strptime(f'{year}-{shown}', '%Y-%j').month

    table_data = []
    for user_id in rows:
        user_days = daily_counts.get(user_id, {})
        if time_period == 'month':
            counts = [user_days.get(f'{year}-{month:02}-{day:02}', 0) for day in range(1, days + 1)]
        else:
            month_totals = defaultdict(int)  # 'YYYY-MM-DD' -> month at positions 5:7
            for day_str, day_count in user_days.items():
                month_totals[int(day_str[5:7])] += day_count
            counts = [month_totals.get(m, 0) for m in range(1, 13)]
        cells = [str(c) if c else '·' for c in counts[:steps_shown]] + [''] * (len(header) - steps_shown)
        table_data.append([short_name(names[user_id])] + cells + [str(totals[user_id])])

    with plt.rc_context(STYLE):
        table_height = 0.5 * (len(rows) + 1)
        fig, (ax_table, ax_lines) = plt.subplots(
            2, 1, figsize=(12, table_height + 9),
            gridspec_kw={'height_ratios': [table_height, 8], 'hspace': 0.3})

        # Table: header row, name column and total column stand out; every row wears its user's colour
        name_width = 0.16
        total_width = 0.10
        step_width = (1 - name_width - total_width) / len(header)
        table = ax_table.table(cellText=table_data, colLabels=[''] + header + ['Totale'],
                               colWidths=[name_width] + [step_width] * len(header) + [total_width],
                               cellLoc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(11)  # one size for names, counts and totals
        last = len(header) + 1
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor(SURFACE)
            cell.set_linewidth(1.5)
            if row == 0:
                cell.set_facecolor(HEADER)
                cell.set_edgecolor(HEADER)  # one solid header band, no dividers
                cell.set_text_props(color=SURFACE, weight='bold', fontsize=9)  # 31 day numbers must not touch
                continue
            colour, _ = user_style(colour_order.index(rows[row - 1]))
            if col == 0:
                cell.set_facecolor(mcolors.to_rgba(colour, 0.4))
                cell.set_text_props(ha='left', weight='bold')
                cell.PAD = 0.06
            elif col == last:
                cell.set_facecolor(TOTAL)
                cell.set_text_props(ha='right', weight='bold')
                cell.PAD = 0.12
            elif col > steps_shown:
                cell.set_facecolor(FUTURE)
            else:
                cell.set_facecolor(mcolors.to_rgba(colour, 0.12))
        # Medals (or the plain position) at the left of every total
        badge_x = 1 - total_width * 0.7
        for row, position in enumerate(positions(rank), start=1):
            y = 1 - (row + 0.5) / (len(rows) + 1)
            if position <= 3:
                emoji(ax_table, MEDALS[position - 1], (badge_x, y), 0.2)
            else:
                ax_table.text(badge_x, y, f'{position}°', ha='center', va='center', fontsize=11,
                              color=TEXT_MUTED, transform=ax_table.transAxes, zorder=6)
        ax_table.axis('off')
        ax_table.set_title(f'Classifica di {title}' if month else f'Classifica del {title}')

        # Cumulative counts, up to today for the current period
        x = np.arange(1, shown + 1)
        for user_id in colour_order:
            user_days = daily_counts.get(user_id, {})
            per_day = []
            for day in x:
                if time_period == 'month':
                    count_date = f'{year}-{month:02}-{day:02}'
                else:
                    count_date = datetime.strptime(f'{year}-{day}', '%Y-%j').strftime(STORING_FORMAT)
                per_day.append(user_days.get(count_date, 0))
            colour, line = user_style(colour_order.index(user_id))
            cumulative = np.cumsum(per_day)
            expected = f' → {forecast[user_id]}' if user_id in forecast else ''
            ax_lines.plot(x, cumulative, color=colour, linestyle=line,
                          label=f'{short_name(names[user_id])} ({totals[user_id]}{expected})')
            if user_id in forecast and shown < days:
                ax_lines.plot([x[-1], days], [cumulative[-1], forecast[user_id]], color=colour, linestyle=':',
                              alpha=0.7)
                ax_lines.scatter([days], [forecast[user_id]], s=50, color=SURFACE, edgecolors=colour,
                                 linewidths=2, zorder=4, clip_on=False)
            ax_lines.scatter([x[-1]], [cumulative[-1]], s=70, color=colour, edgecolors=SURFACE,
                             linewidths=2, zorder=4)

        if time_period == 'month':
            ax_lines.set_xticks(range(1, days + 1))
            fine_vlines(ax_lines, range(1, days + 1))
            ax_lines.set_xlabel('Giorno')
        else:
            # Lines at the month starts, names in the middle of each month
            month_starts = [datetime(year, m, 1).timetuple().tm_yday for m in range(1, 13)] + [days + 1]
            ax_lines.set_xticks(month_starts[:-1], labels=[])
            ax_lines.set_xticks([(a + b) / 2 for a, b in zip(month_starts, month_starts[1:])], labels=header,
                                minor=True)
            ax_lines.tick_params(axis='x', which='minor', length=0)
            fine_vlines(ax_lines, month_starts[1:-1])
        ax_lines.set_xlim(1, days)
        # headroom: the leader's line is not cut at the top; a year rounds to hundreds
        step = 10 if time_period == 'month' else 100
        layered_grid(ax_lines, max_total * 1.05, step, fine_step=step // 10)  # thin lines every 💩 (every 10 a year)
        ax_lines.set_ylabel('Totale progressivo')
        ax_lines.set_title('Come è andata giorno per giorno', fontsize=15, weight='normal', color=TEXT_MUTED)
        ax_lines.legend(loc='upper left', ncol=2 if len(rows) > 4 else 1)

        add_cards(fig, [ax_table, ax_lines])
        return png_bytes(fig)

def generate_statistics_chart(statistics, daily_counts, time_period, date):
    """
    Statistics chart: a normal curve per user built from the mean and the variance of the daily counts,
    and a box plot of the daily counts below it.

    Args:
        statistics (list): dicts with 'user' (database.User), 'mean', 'median' and 'variance'.
        daily_counts (dict): {user_id: {'YYYY-MM-DD': count}} for the period (see database.get_daily_counts).
        time_period (str): 'month' or 'year'.
        date (str): 'MM-YYYY' or 'YYYY'.

    Returns:
        bytes: the PNG image.
    """
    year, month, days, title = period_info(time_period, date)
    names = {stat['user'].user_id: chart_label(stat['user'].name) for stat in statistics}
    stats = {stat['user'].user_id: stat for stat in statistics}
    users = sorted_by_name(names)

    # Daily counts of every user, from the first day of the period to today (or its last day)
    start = datetime(year, month or 1, 1)
    end = start + timedelta(days=last_day_shown(year, month, days) - 1)
    period_days = [(start + timedelta(days=i)).strftime(STORING_FORMAT) for i in range((end - start).days + 1)]
    user_daily_counts = {user: [daily_counts.get(user, {}).get(day, 0) for day in period_days] for user in users}
    max_count = max(max(counts) for counts in user_daily_counts.values())

    with plt.rc_context(STYLE):
        fig, (ax_curves, ax_box) = plt.subplots(2, 1, figsize=(12, 15), gridspec_kw={'hspace': 0.45})

        # Normal curves scaled to the number of days, a dotted line and a label at each mean
        x = np.linspace(0, max(max_count, 1), 200)
        peaks = []
        for i, user in enumerate(users):
            colour, line = user_style(i)
            mean, variance = stats[user]['mean'], stats[user]['variance']
            if variance <= 0:
                continue
            y = normal_pdf(x, mean, np.sqrt(variance)) * len(period_days)
            peak = normal_pdf(mean, mean, np.sqrt(variance)) * len(period_days)
            ax_curves.plot(x, y, color=colour, linestyle=line, label=short_name(names[user]))
            ax_curves.fill_between(x, y, color=colour, alpha=0.05, linewidth=0)
            ax_curves.vlines(mean, 0, peak, colors=colour, linestyles=':', linewidth=1.5)
            peaks.append((mean, peak, colour))
        # Mean labels above the peaks; a label that would cover another one moves up, joined by a thin line
        top = max((peak for _, peak, _ in peaks), default=1)
        width, height = 0.13 * max(max_count, 1), 0.09 * top  # label size in data units, roughly
        placed = []
        for mean, peak, colour in sorted(peaks, key=lambda p: p[1]):
            label_y = peak + height * 0.6
            for other_x, other_y in sorted(placed, key=lambda p: p[1]):
                if abs(mean - other_x) < width and abs(label_y - other_y) < height:
                    label_y = other_y + height
            placed.append((mean, label_y))
            ax_curves.annotate(decimal(mean), (mean, peak), xytext=(mean, label_y), ha='center', va='center',
                               fontsize=11, weight='bold', color=TEXT,
                               arrowprops={'arrowstyle': '-', 'color': colour, 'lw': 1, 'shrinkA': 0, 'shrinkB': 0},
                               bbox={'boxstyle': 'round,pad=0.3', 'fc': SURFACE, 'ec': colour, 'lw': 1.5})
        ax_curves.set_xlim(0, max(max_count, 1))
        fine_vlines(ax_curves, range(0, max(max_count, 1) + 1))
        layered_grid(ax_curves, max([top] + [y for _, y in placed]) + height, 5)  # headroom for the labels
        ax_curves.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax_curves.set_xlabel('Volte al giorno')
        ax_curves.set_ylabel('Giorni')
        ax_curves.set_title(f'Statistiche di {title}' if month else f'Statistiche del {title}')
        if peaks:  # no legend when there are no curves (zero variance)
            ax_curves.legend(loc='upper right', ncol=2 if len(peaks) > 4 else 1)

        # Box plot: box = middle half of the days, line = median, diamond = mean
        box_plot = ax_box.boxplot([user_daily_counts[user] for user in users],
                                  labels=[short_name(names[user]) for user in users], patch_artist=True, widths=0.55,
                                  showmeans=True,
                                  meanprops={'marker': 'D', 'markerfacecolor': SURFACE,
                                             'markeredgecolor': TEXT, 'markersize': 9},
                                  medianprops={'color': TEXT, 'linewidth': 2.5},
                                  flierprops={'marker': 'o', 'markersize': 7, 'alpha': 0.7})
        for i, patch in enumerate(box_plot['boxes']):
            colour, _ = user_style(i)
            patch.set_facecolor(mcolors.to_rgba(colour, 0.35))
            patch.set_edgecolor(colour)
            patch.set_linewidth(2)
            for part in ('whiskers', 'caps'):
                for artist in box_plot[part][i * 2:i * 2 + 2]:
                    artist.set_color(colour)
                    artist.set_linewidth(2)
            box_plot['fliers'][i].set_markeredgecolor(colour)
            box_plot['fliers'][i].set_markerfacecolor(colour)
        ax_box.set_yticks(np.arange(0, max_count + 2, 1))
        ax_box.set_ylim(-0.3, max_count + 0.6)
        ax_box.set_ylabel('Volte al giorno')
        ax_box.tick_params(axis='x', labelsize=13, colors=TEXT)
        ax_box.set_title('Distribuzione giornaliera  (◆ media, — mediana)', fontsize=15, weight='normal',
                         color=TEXT_MUTED)

        add_cards(fig, [ax_curves, ax_box])
        return png_bytes(fig)
