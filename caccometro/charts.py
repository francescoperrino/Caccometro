"""Charts of /leaderboard_* and /stats_*: one shared style, PNG bytes in memory."""
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
from matplotlib import font_manager, patheffects
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MaxNLocator
import numpy as np

from caccometro import __version__, i18n
from caccometro.config import now_rome, STORING_FORMAT
from caccometro.i18n import month_name, tr

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
WATERMARK = '#a99b8a'   # the version under the last card: light, but readable on BACKGROUND

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


def _add_watermark(fig, credit=''):
    """'Caccometro vX.Y.Z' (and the credit of the map data, if any) in small light text centred in the strip between the last card and the bottom of the image.

    png_bytes crops 0.35 inch under the cards (pad_inches); the text is left out of the crop calculation
    (set_in_layout) so that it uses that strip instead of making the image taller.
    """
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_tightbbox(renderer).transformed(fig.transFigure.inverted()) for ax in fig.axes]
    pad = 0.015  # the padding add_cards gives the cards
    strip = 0.35 / fig.get_size_inches()[1]  # pad_inches of png_bytes, as a fraction of the height
    text = fig.text(max(b.x1 for b in boxes) + pad, min(b.y0 for b in boxes) - pad - strip / 2,
                    f'Caccometro v{__version__}' + (f' · {credit}' if credit else ''), ha='right', va='center', fontsize=8, color=WATERMARK)
    text.set_in_layout(False)


def png_bytes(fig, credit=''):
    """Render a figure to PNG in memory and close it."""
    _add_watermark(fig, credit)
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=110, bbox_inches='tight', pad_inches=0.35)
    plt.close(fig)
    return buffer.getvalue()

def _normal_pdf(x, mean, std):
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

def _user_style(i):
    """Colour and line style of the i-th user (users sorted by name, so a user keeps the colour across charts)."""
    return PALETTE[i % len(PALETTE)], '-' if i < len(PALETTE) else '--'

def _decimal(value):
    """Two decimals, with the decimal comma in Italian: 1.25 -> '1,25' ('1.25' in English)."""
    text = f'{value:.2f}'
    return text.replace('.', ',') if i18n.current() == 'it' else text

def _period_info(time_period, date):
    """Year, month (None for a year), number of days and title of the period."""
    if time_period == 'month':
        month, year = (int(part) for part in date.split('-'))
        return year, month, calendar.monthrange(year, month)[1], f'{month_name(month)} {year}'
    year = int(date)
    return year, None, 366 if calendar.isleap(year) else 365, str(year)

def _last_day_shown(year, month, days):
    """Days of the period to draw: all of a past period, up to today for the current one."""
    today = now_rome()
    if year == today.year and (month is None or month == today.month):
        return today.timetuple().tm_yday if month is None else today.day
    return days

FINE_GRID = '#f1e8dc'   # thin lines at every unit, behind the main grid


def _fine_vlines(ax, xs):
    """Thin vertical grid lines at the x positions `xs`."""
    for x in xs:
        ax.axvline(x, color=FINE_GRID, linewidth=0.6, zorder=0)

def _layered_grid(ax, top, round_to, fine_step=None):
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

def _emoji(ax, image, xy, zoom, coords='axes fraction'):
    """Draw an emoji image centred on xy."""
    ax.add_artist(AnnotationBbox(OffsetImage(image, zoom=zoom), xy, xycoords=coords, frameon=False,
                                 zorder=6, annotation_clip=False))

def _positions(rank):
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
        rank (list): (model.User, total) pairs, best first.
        daily_counts (dict): {user_id: {'YYYY-MM-DD': count}} for the period (see database.get_daily_counts).
        time_period (str): 'month' or 'year'.
        date (str): 'MM-YYYY' or 'YYYY'.
        forecast (dict): {user_id: expected total at the end of the period}, drawn as a dotted line from
            today to the last day (see analysis.forecast_totals); None for a past period.

    Returns:
        bytes: the PNG image.
    """
    forecast = forecast or {}
    year, month, days, title = _period_info(time_period, date)
    shown = _last_day_shown(year, month, days)
    names = {user.user_id: chart_label(user.name) for user, _ in rank}
    colour_order = sorted_by_name(names)  # colours follow the user, not the position in the ranking
    totals = {user.user_id: total for user, total in rank}
    rows = [user.user_id for user, _ in rank]  # table rows in ranking order, leader first
    max_total = max(list(totals.values()) + list(forecast.values()), default=0)

    if time_period == 'month':
        header = [str(day) for day in range(1, days + 1)]
        steps_shown = shown
    else:
        header = [month_name(number)[:3].lower() for number in range(1, 13)]  # 'gen', 'feb'... or 'jan', 'feb'...
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
        table = ax_table.table(cellText=table_data, colLabels=[''] + header + [tr('Totale')],
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
            colour, _ = _user_style(colour_order.index(rows[row - 1]))
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
        for row, position in enumerate(_positions(rank), start=1):
            y = 1 - (row + 0.5) / (len(rows) + 1)
            if position <= 3:
                _emoji(ax_table, MEDALS[position - 1], (badge_x, y), 0.2)
            else:
                ax_table.text(badge_x, y, f'{position}°', ha='center', va='center', fontsize=11,
                              color=TEXT_MUTED, transform=ax_table.transAxes, zorder=6)
        ax_table.axis('off')
        ax_table.set_title((tr('Classifica di {title}') if month else tr('Classifica del {title}')).format(title=title))

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
            colour, line = _user_style(colour_order.index(user_id))
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
            _fine_vlines(ax_lines, range(1, days + 1))
            ax_lines.set_xlabel(tr('Giorno'))
        else:
            # Lines at the month starts, names in the middle of each month
            month_starts = [datetime(year, m, 1).timetuple().tm_yday for m in range(1, 13)] + [days + 1]
            ax_lines.set_xticks(month_starts[:-1], labels=[])
            ax_lines.set_xticks([(a + b) / 2 for a, b in zip(month_starts, month_starts[1:])], labels=header,
                                minor=True)
            ax_lines.tick_params(axis='x', which='minor', length=0)
            _fine_vlines(ax_lines, month_starts[1:-1])
        ax_lines.set_xlim(1, days)
        # headroom: the leader's line is not cut at the top; a year rounds to hundreds
        step = 10 if time_period == 'month' else 100
        _layered_grid(ax_lines, max_total * 1.05, step, fine_step=step // 10)  # thin lines every 💩 (every 10 a year)
        ax_lines.set_ylabel(tr('Totale progressivo'))
        ax_lines.set_title(tr('Come è andata giorno per giorno'), fontsize=15, weight='normal', color=TEXT_MUTED)
        ax_lines.legend(loc='upper left', ncol=2 if len(rows) > 4 else 1)

        add_cards(fig, [ax_table, ax_lines])
        return png_bytes(fig)

def generate_statistics_chart(statistics, daily_counts, time_period, date):
    """
    Statistics chart: a normal curve per user built from the mean and the variance of the daily counts,
    and a box plot of the daily counts below it.

    Args:
        statistics (list): dicts with 'user' (model.User), 'mean', 'median' and 'variance'.
        daily_counts (dict): {user_id: {'YYYY-MM-DD': count}} for the period (see database.get_daily_counts).
        time_period (str): 'month' or 'year'.
        date (str): 'MM-YYYY' or 'YYYY'.

    Returns:
        bytes: the PNG image.
    """
    year, month, days, title = _period_info(time_period, date)
    names = {stat['user'].user_id: chart_label(stat['user'].name) for stat in statistics}
    stats = {stat['user'].user_id: stat for stat in statistics}
    users = sorted_by_name(names)

    # Daily counts of every user, from the first day of the period to today (or its last day)
    start = datetime(year, month or 1, 1)
    end = start + timedelta(days=_last_day_shown(year, month, days) - 1)
    period_days = [(start + timedelta(days=i)).strftime(STORING_FORMAT) for i in range((end - start).days + 1)]
    user_daily_counts = {user: [daily_counts.get(user, {}).get(day, 0) for day in period_days] for user in users}
    max_count = max(max(counts) for counts in user_daily_counts.values())

    with plt.rc_context(STYLE):
        fig, (ax_curves, ax_box) = plt.subplots(2, 1, figsize=(12, 15), gridspec_kw={'hspace': 0.45})

        # Normal curves scaled to the number of days, a dotted line and a label at each mean
        x = np.linspace(0, max(max_count, 1), 200)
        peaks = []
        for i, user in enumerate(users):
            colour, line = _user_style(i)
            mean, variance = stats[user]['mean'], stats[user]['variance']
            if variance <= 0:
                continue
            y = _normal_pdf(x, mean, np.sqrt(variance)) * len(period_days)
            peak = _normal_pdf(mean, mean, np.sqrt(variance)) * len(period_days)
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
            ax_curves.annotate(_decimal(mean), (mean, peak), xytext=(mean, label_y), ha='center', va='center',
                               fontsize=11, weight='bold', color=TEXT,
                               arrowprops={'arrowstyle': '-', 'color': colour, 'lw': 1, 'shrinkA': 0, 'shrinkB': 0},
                               bbox={'boxstyle': 'round,pad=0.3', 'fc': SURFACE, 'ec': colour, 'lw': 1.5})
        ax_curves.set_xlim(0, max(max_count, 1))
        _fine_vlines(ax_curves, range(0, max(max_count, 1) + 1))
        _layered_grid(ax_curves, max([top] + [y for _, y in placed]) + height, 5)  # headroom for the labels
        ax_curves.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax_curves.set_xlabel(tr('Volte al giorno'))
        ax_curves.set_ylabel(tr('Giorni'))
        ax_curves.set_title((tr('Statistiche di {title}') if month else tr('Statistiche del {title}')).format(title=title))
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
            colour, _ = _user_style(i)
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
        ax_box.set_ylabel(tr('Volte al giorno'))
        ax_box.tick_params(axis='x', labelsize=13, colors=TEXT)
        ax_box.set_title(tr('Distribuzione giornaliera  (◆ media, — mediana)'), fontsize=15, weight='normal',
                         color=TEXT_MUTED)

        add_cards(fig, [ax_curves, ax_box])
        return png_bytes(fig)


ASSETS = Path(__file__).resolve().parent.parent / 'assets'
ICONS = {name: plt.imread(EMOJI_DIR / f'{name}.png') for name in ('poop', 'trophy', 'fire')}
MASCOT = ASSETS / 'brand' / 'mascot.png'
RECAP_STYLE = 'generated'  # backgrounds of the recap: 'generated' (made with an image generator) or 'code' (drawn shapes)

# Everything the recap picture is made of (#195), as tuned in the design editor. Lengths in inches (the picture is
# 6 x 7.5, 180 px each), font sizes in points; margin, padding and panel_radius are multiples of 'unit'. The picture is
# full bleed: 'margin' is only the room between its edge and the texts.
RECAP = {
    'background': BACKGROUND, 'card': SURFACE, 'text': TEXT, 'up': '#2f9e55', 'down': '#d8573f', 'even': TEXT_MUTED,
    'unit': 0.2, 'margin': 1, 'padding': 2, 'panel_radius': 2.5,
    'avatar': 2.0, 'total': 0.8, 'fact': 0.66, 'tile_alpha': 0.55, 'gap': 0.1,
    'brand_size': 18, 'month_size': 11, 'name_size': 30, 'line_size': 20, 'total_size': 40, 'detail_size': 12,
    'badge_size': 12, 'value_size': 22, 'label_size': 11, 'version_size': 10, 'name_max': 18,
}
# Gradient behind the background picture, top to bottom; the facts take the bottom colour
RECAP_THEMES = {
    1: ('#5b86c0', '#1d3566'), 2: ('#7a78c4', '#2b2f6e'), 3: ('#58b8a2', '#26636f'), 4: ('#e07fae', '#6e4a9e'),
    5: ('#62bb78', '#27705a'), 6: ('#3bb8dc', '#1a64ad'), 7: ('#2cc3bd', '#10648f'), 8: ('#f0925a', '#9a3f7e'),
    9: ('#cf8230', '#6e3418'), 10: ('#cf6a2a', '#5e2418'), 11: ('#b8613e', '#3b2430'), 12: ('#3a64b4', '#13224f'),
    None: ('#8a5ce6', '#1f1b6e'),  # the year
}
PX = 180  # pixels per inch of the recap picture


def _rounded(ax, x, y, w, h, radius, **style):
    patch = FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={radius}', **style)
    ax.add_patch(patch)
    return patch


def _picture(ax, image, x, y, w, h, clip=None, zorder=2):
    """An image filling the box (x, y, w, h), cropped to its proportions like CSS cover."""
    rows, cols = image.shape[:2]
    if cols / rows > w / h:
        keep = round(rows * w / h)
        image = image[:, (cols - keep) // 2:(cols - keep) // 2 + keep]
    else:
        keep = round(cols * h / w)
        image = image[(rows - keep) // 2:(rows - keep) // 2 + keep]
    shown = ax.imshow(image, extent=(x, x + w, y + h, y), zorder=zorder, interpolation='antialiased')
    if clip is not None:
        shown.set_clip_path(clip)
    return shown


def _fade(ax, x, y, w, h, colours, clip, zorder=1):
    """A vertical gradient through `colours` (RGBA tuples, top to bottom) on the box, clipped."""
    ramp = mcolors.LinearSegmentedColormap.from_list('ramp', colours)(np.linspace(0, 1, 256))[:, None, :]
    ax.imshow(ramp, extent=(x, x + w, y + h, y), aspect='auto', zorder=zorder, interpolation='bilinear').set_clip_path(clip)


def generate_recap_image(recap, name):
    """The picture of the recap (#195) to share: 1080x1350 (4:5, what Telegram shows whole), PNG bytes.

    A panel with the picture of the month (or of the year) holds the mascot, the total, the name, the place and the change
    from the period before, then two boxes with the best day and the longest streak. The look is set by RECAP.
    """
    r = RECAP
    year_recap = recap.month is None
    width, height = 6, 7.5
    m, pad, gap = r['margin'] * r['unit'], r['padding'] * r['unit'], r['gap']
    radius = r['panel_radius'] * r['unit']
    pw, ph = width - 2 * m, height - 2 * m
    inner, ix, cx = pw - 2 * pad, m + pad, width / 2
    half = (inner - gap) / 2
    top_colour, bottom_colour = RECAP_THEMES[recap.month]
    period = str(recap.year) if year_recap else f'{month_name(recap.month)} {recap.year}'
    delta = recap.total - recap.previous_total
    if year_recap:
        before = tr("sul {year}").format(year=recap.year - 1)
    else:
        before = tr("su {month}").format(month=month_name(12 if recap.month == 1 else recap.month - 1))
    badge = (f'▲ +{delta}' if delta > 0 else f'▼ −{-delta}' if delta < 0 else '= 0') + ' ' + before
    if recap.people > 1:
        line = tr("{place}° posto su {total}!").format(place=recap.place, total=recap.people)
    else:
        line = tr("che anno!") if year_recap else tr("che mese!")
    detail = ' · '.join([tr("{value} al giorno").format(value=_decimal(recap.total / recap.days)[:-1].removesuffix(',0').removesuffix('.0'))]
                        + ([tr(recap.regularity)] if recap.regularity else []))
    facts = [(ICONS['trophy'], str(recap.best_count),
              tr("il {day} {month}").format(day=recap.best_day.day, month=month_name(recap.best_day.month))),
             (ICONS['fire'], str(recap.streak_days), tr("giorno di fila") if recap.streak_days == 1 else tr("giorni di fila"))]
    outline = [patheffects.withStroke(linewidth=1.2, foreground=(0, 0, 0, .35))]
    with plt.rc_context(STYLE):
        fig = plt.figure(figsize=(width, height), facecolor=r['background'])
        ax = fig.add_axes((0, 0, 1, 1))
        ax.axis('off')
        ax.set_xlim(0, width)
        ax.set_ylim(height, 0)

        def text(x, y, value, size, colour=r['card'], weight='normal', alpha=1, ha='left', stroke=False, **more):
            ax.text(x, y, value, fontsize=size, color=colour, fontweight=weight, alpha=alpha, ha=ha, va='center', zorder=5,
                    path_effects=outline if stroke else None, **more)

        # the panel: the gradient of the month, its picture, darker at the top and bottom so the white texts stay readable
        panel = _rounded(ax, 0, 0, width, height, 0, facecolor='none', edgecolor='none')  # full bleed: no frame around the picture (#214)
        _fade(ax, 0, 0, width, height, [top_colour, bottom_colour], panel)
        background = ASSETS / 'recap' / RECAP_STYLE / ('year.jpg' if year_recap else f'{recap.month:02d}.jpg')
        _picture(ax, plt.imread(background), 0, 0, width, height, clip=panel)
        if RECAP_STYLE == 'generated':  # the drawn backgrounds are calm enough without
            _fade(ax, 0, 0, width, m + 1.5, [(0, 0, 0, .4), (0, 0, 0, 0)], panel, zorder=3)
            _fade(ax, 0, height - m - 2.3, width, m + 2.3, [(0, 0, 0, 0), (0, 0, 0, .42)], panel, zorder=3)
        # the header: the bot on the left, the period on the right
        y = m + 0.55
        _emoji(ax, ICONS['poop'], (ix + 0.17, y), 56 / (128 * PX / 72), coords='data')
        text(ix + 0.5, y, 'Caccometro', r['brand_size'], weight=800, stroke=True)
        text(ix + inner, y, tr("RIEPILOGO {period}").format(period=period.upper()), r['month_size'], weight='bold', alpha=.9,
             ha='right', stroke=True)
        # the mascot on a light plate with a soft shadow, and the total on a pill across its bottom edge
        side, avatar_top = r['avatar'], m + 0.9
        corner = side * 0.2
        for dy, colour in ((0.06, (0, 0, 0, .2)), (0, r['card'])):
            _rounded(ax, cx - side / 2 - 0.07, avatar_top - 0.07 + dy, side + 0.14, side + 0.14, corner + 0.07, facecolor=colour,
                     edgecolor='none', zorder=4)
        frame = _rounded(ax, cx - side / 2, avatar_top, side, side, corner, facecolor='none', edgecolor='none', zorder=4)
        _picture(ax, plt.imread(MASCOT), cx - side / 2, avatar_top, side, side, clip=frame, zorder=4)
        pill_h, pill_y = r['total'], avatar_top + side - r['total'] * 0.25
        for dy, colour in ((0.06, (0, 0, 0, .2)), (0, r['card'])):
            _rounded(ax, cx - 1.25, pill_y + dy, 2.5, pill_h, pill_h / 2, facecolor=colour, edgecolor='none', zorder=4)
        _emoji(ax, ICONS['poop'], (cx - 0.75, pill_y + pill_h / 2), pill_h * PX * 0.62 / (128 * PX / 72), coords='data')
        text(cx + 0.28, pill_y + pill_h / 2, str(recap.total), r['total_size'], colour=r['text'], weight=800, ha='center')
        # who, how it went and the change from the period before
        y = avatar_top + side + r['total'] * 0.75 + 0.38
        text(cx, y, name if len(name) <= r['name_max'] else name[:r['name_max'] - 1] + '…', r['name_size'], weight=800, ha='center')
        text(cx, y + 0.38, line, r['line_size'], weight='bold', alpha=.9, ha='center')
        text(cx, y + 0.76, badge, r['badge_size'], colour='white', weight='bold', ha='center',
             bbox=dict(boxstyle='round,pad=0.45,rounding_size=0.95', edgecolor='none',
                       facecolor=r['up'] if delta > 0 else r['down'] if delta < 0 else r['even']))
        text(cx, y + 1.08, detail, r['detail_size'], alpha=.75, ha='center')
        # the facts, side by side at the bottom of the panel
        tile_h = r['fact']
        tile_y = m + ph - 0.35 - (2 * tile_h + gap) + (tile_h + gap) / 2
        for i, (icon, value, label) in enumerate(facts):
            x = ix + i * (half + gap)
            _rounded(ax, x, tile_y, half, tile_h, min(radius * 0.45, tile_h / 2), facecolor=mcolors.to_rgba(bottom_colour, r['tile_alpha']),
                     edgecolor=(1, 1, 1, .3), linewidth=0.8, zorder=4)
            ax.add_patch(plt.Circle((x + 0.4, tile_y + tile_h / 2), tile_h * 0.38, facecolor=(1, 1, 1, .2), edgecolor='none', zorder=4))
            _emoji(ax, icon, (x + 0.4, tile_y + tile_h / 2), tile_h * PX * 0.5 / (128 * PX / 72), coords='data')
            text(x + 0.85, tile_y + tile_h * 0.35, value, r['value_size'], weight=800)
            text(x + 0.85, tile_y + tile_h * 0.73, label, r['label_size'], alpha=.8)
        text(ix + inner, m + ph - 0.2, f'Caccometro v{__version__}', r['version_size'], alpha=.75, ha='right', stroke=True)
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=PX, facecolor=r['background'])
        plt.close(fig)
        return buffer.getvalue()
