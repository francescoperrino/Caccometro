"""Download db/*.db from the hosting into backups/db/<stamp>/ and keep only the newest copies.

Usage: python tools/backup_db.py [--keep N]
Besides the daily copies, the first copy of each month is also kept for good in backups/db_monthly/<YYYYMM>/ (about 300 KB each).
Fails (like any other error) when the total count of a chat dropped by more than 20% since the previous copy; that copy is
kept but not promoted to a monthly one.
Meant for a daily cron job on the development machine (settings: see deploy.py). Exit code 1 (and a line on stderr) when
anything fails, so a failed backup is visible. Reuses the download code of deploy.py.
A failure is also sent as a private Telegram message through the bot of BOT_TOKEN (the development bot in the local .env) to
ALERT_CHAT_ID (the maintainer's chat with it); nothing is sent when the backup works or when ALERT_CHAT_ID is not set.
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import httpx

from deploy import FILES, REPO, download, token

KEEP = 14
MAX_DROP = 0.2  # a legitimate /togli removes a few; losing a fifth of a chat's total is not normal
MIN_TOTAL = 10  # below this a single /togli is already a big relative drop


def alert(text):
    """Tell the maintainer on Telegram; never raises and never prints the token (httpx errors carry the URL)."""
    chat, bot = os.environ.get("ALERT_CHAT_ID"), os.environ.get("BOT_TOKEN")
    if not (chat and bot):
        return
    try:
        httpx.post(f"https://api.telegram.org/bot{bot}/sendMessage", data={"chat_id": chat, "text": text}, timeout=20)
    except httpx.HTTPError:
        pass  # the FAILED line on stderr and in the log is still there


def total(path):
    with sqlite3.connect(path) as conn:
        try:
            return conn.execute("SELECT COALESCE(SUM(count), 0) FROM user_count").fetchone()[0]
        except sqlite3.OperationalError:  # no counts table: nothing to compare
            return None


def drops(previous, folder, names):
    found = []
    for n in names:
        if not (previous / n).exists():
            continue  # new chat, or renamed by a supergroup upgrade
        old, new = total(previous / n), total(folder / n)
        if old is not None and new is not None and old >= MIN_TOTAL and new < old * (1 - MAX_DROP):
            found.append(f"{n}: total {old} -> {new}")
    return found


def main(keep):
    folder = REPO / "backups" / "db" / datetime.now().strftime("%Y%m%d_%H%M%S")
    previous = max((p for p in folder.parent.iterdir() if p.is_dir()), default=None) if folder.parent.exists() else None
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
    found = drops(previous, folder, names) if previous else []
    monthly = REPO / "backups" / "db_monthly" / folder.name[:6]
    if not found and not monthly.exists():
        shutil.copytree(folder, monthly)
    for old in sorted(p for p in folder.parent.iterdir() if p.is_dir())[:-keep]:
        shutil.rmtree(old)
    if found:
        sys.exit(f"{datetime.now():%Y-%m-%d %H:%M} backup FAILED: counts dropped sharply since {previous.name}: {'; '.join(found)}")
    print(f"{datetime.now():%Y-%m-%d %H:%M} backup ok: {len(names)} databases in {folder}")


if __name__ == "__main__":
    keep = int(sys.argv[sys.argv.index("--keep") + 1]) if "--keep" in sys.argv else KEEP
    message = None
    try:
        main(keep)
    except (httpx.HTTPError, OSError, sqlite3.Error) as e:
        message = f"{datetime.now():%Y-%m-%d %H:%M} backup FAILED: {e!r}"
    except SystemExit as e:  # main() exits with a message for its own failures
        if isinstance(e.code, str):
            message = e.code if "FAILED" in e.code else f"{datetime.now():%Y-%m-%d %H:%M} backup FAILED: {e.code}"
    if message:
        alert(f"Caccometro: {message}")
        sys.exit(message)
