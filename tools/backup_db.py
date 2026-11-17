"""Download db/*.db from the hosting into backups/db/<stamp>/ and keep only the newest copies.

Usage: python tools/backup_db.py [--keep N]
Meant for a daily cron job on the development machine (settings: see deploy.py). Exit code 1 (and a line on stderr) when
anything fails, so a failed backup is visible. Reuses the download code of deploy.py.
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import httpx

from deploy import FILES, REPO, download, token

KEEP = 14


def main(keep):
    folder = REPO / "backups" / "db" / datetime.now().strftime("%Y%m%d_%H%M%S")
    with httpx.Client(headers={"Authorization": f"Token {token()}"}, timeout=120) as client:
        listing = client.get(f"{FILES}/db/")
        listing.raise_for_status()
        names = [n for n, info in listing.json().items() if info["type"] == "file" and n.endswith(".db")]
        if not names:
            sys.exit("no databases found on the hosting")
        for n in names:
            if not download(client, f"db/{n}", folder / n):
                sys.exit(f"{n}: not found on the hosting")
            with sqlite3.connect(folder / n) as conn:  # a truncated or corrupt copy must fail loudly
                if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    sys.exit(f"{n}: integrity check failed")
    for old in sorted(p for p in folder.parent.iterdir() if p.is_dir())[:-keep]:
        shutil.rmtree(old)
    print(f"{datetime.now():%Y-%m-%d %H:%M} backup ok: {len(names)} databases in {folder}")


if __name__ == "__main__":
    keep = int(sys.argv[sys.argv.index("--keep") + 1]) if "--keep" in sys.argv else KEEP
    try:
        main(keep)
    except (httpx.HTTPError, OSError, sqlite3.Error) as e:
        sys.exit(f"{datetime.now():%Y-%m-%d %H:%M} backup FAILED: {e!r}")
