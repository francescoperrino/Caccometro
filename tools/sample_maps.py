"""Draw the conquest maps shown in the README with the bot's own code, from fixed fake conquests.

Usage: python tools/sample_maps.py  (run by hand: it fetches OpenStreetMap tiles, so the pre-commit hook leaves it out)
Writes assets/screenshots/conquest_<view>_<language>.jpg.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from caccometro import i18n, maps  # noqa: E402
from caccometro.conquest import cell_of  # noqa: E402
from caccometro.model import User  # noqa: E402

OUT = REPO / "assets" / "screenshots"
PEOPLE = {1: User(1, "giulia", "Giulia"), 2: User(2, "marco", "Marco"), 3: User(3, None, "Anna")}  # Anna: no username
CONQUESTS = [  # (latitude, longitude, user_id), in order: the last one is the conquest just made
    (45.4642, 9.19, 1), (45.4780, 9.23, 1), (45.452, 9.15, 3), (45.49, 9.19, 2), (45.435, 9.22, 2),
    (45.52, 9.22, 3), (45.5845, 9.2744, 2), (45.44, 9.10, 1), (45.0703, 7.6869, 1), (44.4056, 8.9463, 1),
    (44.4949, 11.3426, 2), (43.7696, 11.2558, 2), (45.4408, 12.3155, 3), (41.9028, 12.4964, 2), (41.88, 12.52, 3),
    (40.8518, 14.2681, 3), (41.1171, 16.8719, 1), (38.1157, 13.3615, 3), (37.5079, 15.083, 2), (39.2238, 9.1217, 1),
    (48.8566, 2.3522, 1), (51.5072, -0.1276, 3), (40.7128, -74.006, 1), (35.6762, 139.6503, 3), (45.47, 9.20, 2),
]


def main():
    history = [(user_id, cell_of(lat, lon)) for lat, lon, user_id in CONQUESTS]
    for language in ("it", "en"):
        i18n.use(language)
        for view in ("zoom", "region", "country", "world"):
            path = OUT / f"conquest_{view}_{language}.jpg"
            path.write_bytes(getattr(maps, f"{view}_map")(history, PEOPLE))
            print(path.relative_to(REPO))


if __name__ == "__main__":
    main()
