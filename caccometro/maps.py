"""Conquest maps (#157): the tiles of a chat drawn over OpenStreetMap raster tiles, JPEG bytes in memory.

Four views, each a level of the h3 grid: the zoom around a conquest (resolution 6, the real tiles), and for
/conquests Lombardy (resolution 5), Italy (resolution 4) and the world (resolution 1), on fixed boxes. At the larger levels a hexagon stands for the
tiles it contains: ownership, counts and the king stay at resolution 6.
"""
import io
import logging
import math
import os
import time

import h3
import httpx
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from PIL import Image

from caccometro import __version__
from caccometro.charts import PALETTE, STYLE, TEXT, add_cards, chart_label, png_bytes, short_name, sorted_by_name
from caccometro.config import PROJECT_DIR
from caccometro.conquest import holdings, mention_of
from caccometro.i18n import tr

logger = logging.getLogger(__name__)

TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
# The tile usage policy wants the application identified; no personal contact
USER_AGENT = f'Caccometro/{__version__} (+https://github.com/francescoperrino/Caccometro)'
CREDIT = '© OpenStreetMap contributors'
CACHE_DIR = PROJECT_DIR / 'tile_cache'
CACHE_SECONDS = 7 * 24 * 3600  # the policy asks to keep tiles at least 7 days
CACHE_MAX_FILES = 3000         # about 20 KB each: some 60 MB of the 512 MB disk quota
REQUEST_TIMEOUT = 4            # seconds per tile
FETCH_BUDGET = 10              # seconds for all the tiles of an image; then the reply goes out as text
TILE_SIZE = 256
MAX_LAT = 85.0511              # Web Mercator ends here

ZOOM_LEVEL, ZOOM_SPAN = 11, 2.5          # conquest reply: about 9 map tiles around the new tile
# /conquests: (h3 resolution, map zoom, (south, north, west, east)). shortcut: fixed on Lombardy and Italy,
# where the bot is played today; a group elsewhere needs its own boxes
REGION = (5, 8, (44.6, 46.7, 8.4, 11.5))       # Lombardy, about 9 map tiles
COUNTRY = (4, 6, (36.4, 47.2, 6.5, 18.6))      # Italy with the islands, about 12 map tiles
WORLD = (1, 2, (-58, 80, -180, 180))           # the poles and Antarctica cut away


def tile_xy(lat, lon, z):
    """Position of a point in map tile units at zoom z (Web Mercator): x grows east, y grows south."""
    lat = max(-MAX_LAT, min(MAX_LAT, lat))
    n = 2 ** z
    s = math.sin(math.radians(lat))
    return (lon + 180) / 360 * n, (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n


def outline(cell, z):
    """Corners of an h3 cell in tile units, the longitudes unwrapped so a cell across 180° stays in one piece."""
    points, previous = [], None
    for lat, lon in h3.cell_to_boundary(cell):
        if previous is not None:
            lon += 360 * round((previous - lon) / 360)
        previous = lon
        points.append(tile_xy(lat, lon, z))
    return points


def owners(history):
    """{cell: (user_id, index of its latest conquest)}: a tile belongs to its last conqueror."""
    return {cell: (user_id, i) for i, (user_id, cell) in enumerate(history)}


def grouped(tiles, res):
    """{cell at res: user_id}: each hexagon goes to the member holding most tiles inside, on a tie the latest."""
    tally = {}
    for cell, (user_id, i) in tiles.items():
        members = tally.setdefault(h3.cell_to_parent(cell, res), {})
        held, last = members.get(user_id, (0, -1))
        members[user_id] = (held + 1, max(last, i))
    return {parent: max(members, key=members.get) for parent, members in tally.items()}


def cached_tile(z, x, y, client, deadline):
    """One map tile as a PIL image, from the cache when fresh; a stale copy is better than nothing."""
    path = CACHE_DIR / f'{z}_{x}_{y}.png'
    fresh = path.exists() and time.time() - path.stat().st_mtime < CACHE_SECONDS
    if not fresh:
        try:
            if time.time() > deadline:
                raise TimeoutError('tile budget used up')
            for attempt in range(2):  # the hosting proxy gives intermittent 503s; a GET can be repeated
                try:
                    response = client.get(TILE_URL.format(z=z, x=x, y=y))
                    response.raise_for_status()
                    break
                except httpx.HTTPError:
                    if attempt or time.time() > deadline:
                        raise
                    time.sleep(0.5)
            CACHE_DIR.mkdir(exist_ok=True)
            partial = path.with_suffix('.part')
            partial.write_bytes(response.content)
            os.replace(partial, path)
        except Exception:
            if not path.exists():
                raise
            logger.warning(f"Map tile {z}/{x}/{y} not refreshed: using the stale copy")
    return Image.open(path).convert('RGB')


def trim_cache():
    """Drop the oldest tiles when the cache holds more than CACHE_MAX_FILES."""
    files = sorted(CACHE_DIR.glob('*.png'), key=lambda f: f.stat().st_mtime)
    for old in files[:max(0, len(files) - CACHE_MAX_FILES)]:
        old.unlink(missing_ok=True)


def basemap(z, x0, y0, x1, y1):
    """The map tiles covering the box joined in one image, and the box of tile units the image spans."""
    n = 2 ** z
    xs = range(math.floor(x0), math.ceil(x1))
    ys = range(max(0, math.floor(y0)), min(n, math.ceil(y1)))
    image = Image.new('RGB', (TILE_SIZE * len(xs), TILE_SIZE * len(ys)))
    deadline = time.time() + FETCH_BUDGET
    with httpx.Client(headers={'User-Agent': USER_AGENT}, timeout=REQUEST_TIMEOUT) as client:
        for i, x in enumerate(xs):
            for j, y in enumerate(ys):
                image.paste(cached_tile(z, x % n, y, client, deadline), (TILE_SIZE * i, TILE_SIZE * j))
    trim_cache()
    return image, (xs[0], ys[0], xs[-1] + 1, ys[-1] + 1)


def draw(title, z, box, hexagons, colors, legend, latest, grid=()):
    """The map image: hexagons {cell: user_id} in the colours of their members over the map tiles of the box,
    the hexagon `latest` outlined, the cells of `grid` as a faint grid. legend: [(user_id, label)]."""
    image, (ix0, iy0, ix1, iy1) = basemap(z, *box)
    x0, y0, x1, y1 = box
    n = 2 ** z
    with plt.rc_context(STYLE):
        width = 9
        fig, ax = plt.subplots(figsize=(width, width * (y1 - y0) / (x1 - x0)))
        ax.imshow(image, extent=(ix0, ix1, iy1, iy0), interpolation='lanczos')

        def shapes(cell):  # the copies show a hexagon across 180° on both edges of the world
            points = outline(cell, z)
            return [[(x + shift, y) for x, y in points] for shift in (-n, 0, n)]

        def hexagon(cell, **style):
            for points in shapes(cell):
                ax.add_patch(Polygon(points, closed=True, **style))

        # one collection: the grid of a map has hundreds of hexagons
        ax.add_collection(PolyCollection([points for cell in grid for points in shapes(cell)], facecolors='none',
                                         edgecolors='white', linewidths=0.6, alpha=0.8))
        for cell, user_id in hexagons.items():
            hexagon(cell, facecolor=colors[user_id], edgecolor=colors[user_id], alpha=0.5, linewidth=0.9)
        if latest is not None:
            hexagon(latest, fill=False, edgecolor=TEXT, linewidth=2)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y1, y0)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(title)
        handles = [Line2D([], [], marker='h', linestyle='', markersize=13, color=colors[user_id], alpha=0.8, label=label)
                   for user_id, label in legend]
        if latest is not None:
            handles.append(Line2D([], [], marker='h', linestyle='', markersize=13, markerfacecolor='none',
                                  markeredgecolor=TEXT, label=tr('ultima conquista')))
        ax.legend(handles=handles, loc='lower left', fontsize=11)
        add_cards(fig, [ax])
        return jpeg(png_bytes(fig, CREDIT))


def jpeg(png):
    """The image as JPEG: a street map is 1 MB as PNG, a fifth as JPEG, and Telegram recompresses photos anyway."""
    out = io.BytesIO()
    Image.open(io.BytesIO(png)).convert('RGB').save(out, 'JPEG', quality=85)
    return out.getvalue()


def legend_and_colors(history, users):
    """Legend [(user_id, 'name: tiles held')] by tiles held, and a colour per member who ever conquered.

    Colours follow the names, like the charts. shortcut: a 9th member reuses the first colour; fine for a group of friends.
    """
    counts = holdings(history)[0]
    labels = {user_id: chart_label(short_name(mention_of(users, user_id))) for user_id, _ in history}
    colors = {user_id: PALETTE[i % len(PALETTE)] for i, user_id in enumerate(sorted_by_name(labels))}
    ranking = sorted(counts, key=lambda user_id: (-counts[user_id], labels[user_id].lower()))
    legend = [(user_id, f'{labels[user_id]}: {counts[user_id]}') for user_id in ranking]
    return legend, colors


def zoom_map(history, users):
    """Reply to a conquest: the real tiles around the tile just conquered, the last of `history`."""
    tiles = owners(history)
    new_cell = history[-1][1]
    x, y = tile_xy(*h3.cell_to_latlng(new_cell), ZOOM_LEVEL)
    half = ZOOM_SPAN / 2
    around = h3.grid_disk(new_cell, 4)  # wider than the image: hexagons are 7 km, the image about 30 km
    legend, colors = legend_and_colors(history, users)
    return draw(tr('Zona conquistata'), ZOOM_LEVEL, (x - half, y - half, x + half, y + half),
                {cell: tiles[cell][0] for cell in around if cell in tiles}, colors, legend, new_cell,
                grid=[cell for cell in around if cell not in tiles])


def world_map(history, users):
    """/conquests: the whole world."""
    return overview(history, users, tr('Conquiste nel mondo'), *WORLD)


def region_map(history, users):
    """/conquests: Lombardy."""
    return overview(history, users, tr('Conquiste in Lombardia'), *REGION)


def country_map(history, users):
    """/conquests: Italy."""
    return overview(history, users, tr('Conquiste in Italia'), *COUNTRY)


def overview(history, users, title, res, z, bounds):
    """A map of every held tile grouped at resolution res over the bounds (south, north, west, east),
    the parent of the latest conquest outlined."""
    south, north, west, east = bounds
    x0, y1 = tile_xy(south, west, z)
    x1, y0 = tile_xy(north, east, z)
    legend, colors = legend_and_colors(history, users)
    return draw(title, z, (x0, y0, x1, y1), grouped(owners(history), res), colors, legend,
                h3.cell_to_parent(history[-1][1], res), grid=grid_cells(res, bounds))


def grid_cells(res, bounds, margin=0.3):
    """Every cell at res over the bounds, so the map shows the faint grid; the whole world when it spans 360°."""
    south, north, west, east = bounds
    if east - west >= 360:
        return [cell for base in h3.get_res0_cells() for cell in h3.cell_to_children(base, res)]
    south, north, west, east = south - margin, north + margin, west - margin, east + margin
    return h3.polygon_to_cells(h3.LatLngPoly([(south, west), (south, east), (north, east), (north, west)]), res)


def render(builder, *args):
    """builder(*args), or None when the map cannot be drawn (tiles unreachable): the reply then goes out as text."""
    try:
        return builder(*args)
    except Exception as error:
        logger.warning(f"Map {builder.__name__} not drawn, text only: {type(error).__name__}: {error}")
        return None
