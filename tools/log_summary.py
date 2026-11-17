"""Download the logs, print a short summary of the last 24 hours and flag the kinds of errors never seen before.

Usage: python tools/log_summary.py (settings: see deploy.py)
Meant for the nightly cron job, after backup_db.py. The summary is also kept in logs/summary_<date>.txt (the last 30).
A kind of error that is not in KNOWN and was not reported before (logs/seen_kinds.txt) goes out once as a private Telegram
message, like a failed backup (see backup_db.alert). Reads the bot log (caccometro.log) and the access log of the web server.
"""
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROME = ZoneInfo("Europe/Rome")
RECORD = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d{3} - \S+ - (\w+) - (.*)$")
ACCESS = re.compile(r'\[(\d\d/\w{3}/\d{4}:\d\d:\d\d:\d\d) \+0000\] "POST /webhook HTTP/[\d.]+" (\d{3}) .*response-time=([\d.]+)')
REFUSED = "Webhook call without the right secret token"  # counted from the 403s of the access log instead
# Normalized messages (see kind) that are expected: the hosting proxy answers 503 now and then (see RetryingRequest).
KNOWN = (
    'Update "N" caused error "httpx.ProxyError: N Service Unavailable"',
    "Error in webhook: httpx.ProxyError: N Service Unavailable",
)
KEEP = 30


def kind(message):
    """The message without what changes from one occurrence to the next (numbers, usernames)."""
    return re.sub(r"\d+", "N", re.sub(r"@\w+", "@U", message))


def summarize(bot_lines, access_lines, since, until, seen=()):
    """Return (text, new kinds). Times are naive Rome time; lines of tracebacks do not match RECORD and are skipped."""
    updates = retries = lost = refused = 0
    kinds = Counter()
    for line in bot_lines:
        m = RECORD.match(line)
        if not m or not since <= datetime.fromisoformat(m[1]) <= until:
            continue
        level, message = m[2], m[3]
        if message.startswith("Webhook received"):
            updates += 1
        elif message.startswith("Telegram request failed"):
            retries += 1
        elif level in ("WARNING", "ERROR", "CRITICAL") and not message.startswith(REFUSED):
            kinds[kind(message)] += 1
            lost += message.startswith("Update ") and " caused error " in message
    slowest = (0.0, None)
    for line in access_lines:
        m = ACCESS.search(line)
        if not m:
            continue
        when = datetime.strptime(m[1], "%d/%b/%Y:%H:%M:%S").replace(tzinfo=timezone.utc).astimezone(ROME).replace(tzinfo=None)
        if not since <= when <= until:
            continue
        if m[2] == "403":
            refused += 1
        elif m[2] != "200":
            kinds[f"HTTP {m[2]} on POST /webhook"] += 1
        slowest = max(slowest, (float(m[3]), when), key=lambda s: s[0])
    explained = sum(n for k, n in kinds.items() if k.startswith("Error in webhook"))  # each one is answered with a 500
    h500 = "HTTP 500 on POST /webhook"
    if h500 in kinds:
        kinds[h500] -= explained
        if kinds[h500] <= 0:
            del kinds[h500]
    new = [k for k in kinds if not k.startswith(KNOWN) and k not in seen]
    lines = [
        f"Riassunto dei log dal {since:%d/%m %H:%M} al {until:%d/%m %H:%M}",
        f"Update ricevuti: {updates}",
        f"Tentativi ripetuti verso Telegram: {retries}",
        f"Risposte perse (tentativi finiti): {lost}",
        f"Chiamate rifiutate dal webhook: {refused}",
        f"Update piu' lento: {slowest[0]:.1f} s" + (f" alle {slowest[1]:%d/%m %H:%M}" if slowest[1] else ""),
        "Errori:" + (" nessuno" if not kinds else ""),
    ]
    lines += [f"  {n} x {k}" + ("   <-- NUOVO" if k in new else "") for k, n in kinds.most_common()]
    return "\n".join(lines), new


def main():
    from backup_db import alert
    from deploy import REPO
    import fetch_logs

    logs = REPO / "logs"
    failed = fetch_logs.main()
    if failed:
        message = f"download of {', '.join(failed)} failed"
        alert(f"⚠️ Caccometro: riassunto dei log non riuscito\n\n{message}")
        sys.exit(f"log summary FAILED: {message}")
    seen_file = logs / "seen_kinds.txt"
    seen = set(seen_file.read_text(encoding="utf-8").splitlines()) if seen_file.exists() else set()
    now = datetime.now(ROME).replace(tzinfo=None)
    read = lambda name: (logs / name).read_text(encoding="utf-8", errors="replace").splitlines()
    text, new = summarize(read("caccometro.log"), read("access.log"), now - timedelta(hours=24), now, seen)
    print(text)
    summary = logs / f"summary_{now:%Y%m%d}.txt"
    summary.write_text(text + "\n", encoding="utf-8")
    for old in sorted(logs.glob("summary_*.txt"))[:-KEEP]:
        old.unlink()
    if new:
        alert("⚠️ Caccometro: nei log c'e' qualcosa di nuovo\n\n" + "\n".join(k[:200] for k in new[:10]) + f"\n\nRiassunto: {summary}")
        with seen_file.open("a", encoding="utf-8") as f:
            f.writelines(k + "\n" for k in new)


if __name__ == "__main__":
    main()
