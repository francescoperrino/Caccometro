"""Download the logs, print a summary of the last 24 hours and send an alert when something needs a look.

Usage: python tools/log_summary.py (settings: see deploy.py)
Meant for the nightly cron job, after backup_db.py. The summary is also kept in logs/summary_<date>.txt and the
downloaded logs in logs/logs_<date>.tar.gz (the last 30 of each).
Reads the bot log (caccometro.log, mostly the "Update N done" line of every update) and the web server logs
(access, error and server log). One private Telegram message, like a failed backup (see backup_db.alert), lists the
reasons to look: a lost reply, a kind of error never seen (logs/seen_kinds.txt) or repeated, a slow update, lines in
the web server error log.
"""
import re
import statistics
import sys
import tarfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROME = ZoneInfo("Europe/Rome")
RECORD = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d{3} - \S+ - (\w+) - (.*)$")
DONE = re.compile(r"^Update \S+ done: command=(\S+) chat=(\w+) ms=(\d+) attempts=\d+ outcome=(\w+)$")
ACCESS = re.compile(r'\[(\d\d/\w{3}/\d{4}:\d\d:\d\d:\d\d) \+0000\] "(\w+) (\S+) HTTP/[\d.]+" (\d{3}) .*response-time=([\d.]+)')
STAMP = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)")  # error and server log, in UTC
RESTART = "WSGI app 0 (mountpoint='') ready"  # the server log line of every start of the app (deploy, reload)
UPTIME_CHECK = "UptimeRobot"
REFUSED = "Webhook call without the right secret token"  # counted from the 403s of the access log instead
# Normalized messages (see kind) that are expected: the hosting proxy answers 503 now and then (see RetryingRequest).
KNOWN = (
    'Update "N" caused error "httpx.ProxyError: N Service Unavailable"',
    "Error in webhook: httpx.ProxyError: N Service Unavailable",
)
# Slower than this is worth an alert: the reply to a 💩 takes under 1 s, a chart or a map a few seconds
SLOW_MS = {"command": 15_000, "message": 5_000}
KEEP = 30


def kind(message):
    """The message without what changes from one occurrence to the next (numbers, usernames)."""
    return re.sub(r"\d+", "N", re.sub(r"@\w+", "@U", message))


def utc_to_rome(when):
    return when.replace(tzinfo=timezone.utc).astimezone(ROME).replace(tzinfo=None)


def seconds(ms):
    return f"{ms / 1000:.1f} s"


def summarize(bot_lines, access_lines, since, until, seen=(), error_lines=(), server_lines=()):
    """Return (text, new kinds, reasons for an alert).

    Times are naive Rome time; lines of tracebacks do not match RECORD and are skipped.
    """
    retries = refused = 0
    kinds = Counter()
    durations = defaultdict(list)
    chats, outcomes = Counter(), Counter()
    exceptions, slow = [], []
    failing = set()  # kinds of ERROR and CRITICAL lines: only these are worth an alert when repeated
    for line in bot_lines:
        m = RECORD.match(line)
        if not m or not since <= (when := datetime.fromisoformat(m[1])) <= until:
            continue
        level, message = m[2], m[3]
        if done := DONE.match(message):
            command, chat, ms, outcome = done[1], done[2], int(done[3]), done[4]
            durations[command].append(ms)
            chats[chat] += 1
            outcomes[outcome] += 1
            if ms > SLOW_MS["command" if command.startswith("/") else "message"]:
                slow.append(f"{command} {seconds(ms)} alle {when:%d/%m %H:%M}")
        elif message.startswith("Telegram request failed"):
            retries += 1
        elif level in ("WARNING", "ERROR", "CRITICAL") and not message.startswith(REFUSED):
            kinds[kind(message)] += 1
            if level != "WARNING":
                failing.add(kind(message))
                exceptions.append(f"{when:%d/%m %H:%M} {message[:200]}")
    slowest = (0.0, None)
    other_requests = Counter()
    for line in access_lines:
        m = ACCESS.search(line)
        if not m:
            continue
        when = utc_to_rome(datetime.strptime(m[1], "%d/%b/%Y:%H:%M:%S"))
        if not since <= when <= until:
            continue
        method, path, status = m[2], m[3], m[4]
        if (method, path) != ("POST", "/webhook"):
            if UPTIME_CHECK not in line:
                other_requests[f"{method} {path} {status}"] += 1
            continue
        if status == "403":
            refused += 1
        elif status != "200":
            kinds[f"HTTP {status} on POST /webhook"] += 1
        slowest = max(slowest, (float(m[5]), when), key=lambda s: s[0])
    explained = sum(n for k, n in kinds.items() if k.startswith("Error in webhook"))  # each one is answered with a 500
    h500 = "HTTP 500 on POST /webhook"
    if h500 in kinds:
        kinds[h500] -= explained
        if kinds[h500] <= 0:
            del kinds[h500]

    def in_window(lines):
        """The lines of a UTC log that start with a time inside the window, with the time in Rome."""
        for line in lines:
            m = STAMP.match(line)
            if m and since <= (when := utc_to_rome(datetime.fromisoformat(m[1]))) <= until:
                yield when, line

    restarts = [when for when, line in in_window(server_lines) if RESTART in line]
    errors = [line for _, line in in_window(error_lines)]

    new = [k for k in kinds if not k.startswith(KNOWN) and k not in seen]
    repeated = [k for k, n in kinds.items() if not k.startswith(KNOWN) and n >= 2 and k in failing and k not in new]
    lost = outcomes["lost"]
    reasons = ([f"Risposte perse: {lost}"] if lost else []) \
        + [f"Errore nuovo: {k[:200]}" for k in new[:10]] \
        + [f"Errore ripetuto {kinds[k]} volte: {k[:200]}" for k in repeated[:10]] \
        + [f"Update lento: {s}" for s in slow[:10]] \
        + ([f"Righe nell'error log del server: {len(errors)}"] if errors else [])

    total = sum(chats.values())
    lines = [
        f"Riassunto dei log dal {since:%d/%m %H:%M} al {until:%d/%m %H:%M}",
        f"Update ricevuti: {total} (privati {chats['private']}, gruppi {chats['group']})",
        f"Tentativi ripetuti verso Telegram: {retries}",
        f"Risposte perse (tentativi finiti): {lost}",
        f"Update finiti con un errore: {outcomes['error']}",
        f"Chiamate rifiutate dal webhook: {refused}",
        f"Update piu' lento: {slowest[0]:.1f} s" + (f" alle {slowest[1]:%d/%m %H:%M}" if slowest[1] else ""),
        "Comandi (volte, mediana, peggiore):" + (" nessuno" if not durations else ""),
    ]
    lines += [f"  {command}: {len(ms)}, {seconds(statistics.median(ms))}, {seconds(max(ms))}"
              for command, ms in sorted(durations.items(), key=lambda item: -len(item[1]))]
    lines.append("Errori:" + (" nessuno" if not kinds else ""))
    lines += [f"  {n} x {k}" + ("   <-- NUOVO" if k in new else "") for k, n in kinds.most_common()]
    lines.append("Eccezioni:" + (" nessuna" if not exceptions else ""))
    lines += [f"  {e}" for e in exceptions[:20]]
    lines.append(f"Riavvii dell'app: {len(restarts)}" + "".join(f", {when:%d/%m %H:%M}" for when in restarts))
    lines.append(f"Righe nell'error log del server: {len(errors)}")
    lines += [f"  {line[:200]}" for line in errors[:10]]
    lines.append("Altre richieste al server (senza i controlli di UptimeRobot):" + (" nessuna" if not other_requests else ""))
    lines += [f"  {n} x {request}" for request, n in other_requests.most_common(10)]
    return "\n".join(lines), new, reasons


def archive(logs, names, day, keep=KEEP):
    """Keep a compressed copy of the downloaded logs in logs/logs_<day>.tar.gz, the last `keep` of them."""
    with tarfile.open(logs / f"logs_{day:%Y%m%d}.tar.gz", "w:gz") as tar:
        for name in names:
            tar.add(logs / name, arcname=name)
    for old in sorted(logs.glob("logs_*.tar.gz"))[:-keep]:
        old.unlink()


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
    now = datetime.now(ROME).replace(tzinfo=None)
    archive(logs, fetch_logs.LOGS, now)
    seen_file = logs / "seen_kinds.txt"
    seen = set(seen_file.read_text(encoding="utf-8").splitlines()) if seen_file.exists() else set()
    read = lambda name: (logs / name).read_text(encoding="utf-8", errors="replace").splitlines()
    text, new, reasons = summarize(read("caccometro.log"), read("access.log"), now - timedelta(hours=24), now, seen,
                                   read("error.log"), read("server.log"))
    print(text)
    summary = logs / f"summary_{now:%Y%m%d}.txt"
    summary.write_text(text + "\n", encoding="utf-8")
    for old in sorted(logs.glob("summary_*.txt"))[:-KEEP]:
        old.unlink()
    if reasons:
        alert("⚠️ Caccometro: nei log c'e' qualcosa da guardare\n\n" + "\n".join(reasons) + f"\n\nRiassunto: {summary}")
    if new:
        with seen_file.open("a", encoding="utf-8") as f:
            f.writelines(k + "\n" for k in new)


if __name__ == "__main__":
    main()
