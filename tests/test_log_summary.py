"""tools/log_summary.py: counts, commands, known and new kinds of errors, reasons for an alert."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import log_summary as ls  # noqa: E402

SINCE, UNTIL = datetime(2026, 11, 17, 0, 0), datetime(2026, 11, 18, 0, 0)
BOT = """\
2026-11-17 10:00:00,100 - caccometro.webhook - INFO - Webhook received...
2026-11-17 10:00:01,000 - caccometro.bot - WARNING - Telegram request failed (httpx.ProxyError: 503 Service Unavailable), new attempt in 1 s
2026-11-17 10:00:20,000 - caccometro.bot - ERROR - Update "140785497" caused error "httpx.ProxyError: 503 Service Unavailable" in message
Traceback (most recent call last):
2026-11-17 10:00:20,001 - caccometro.bot - INFO - Update 140785497 done: command=message chat=group ms=19900 attempts=6 outcome=lost
2026-11-17 10:00:21,000 - caccometro.webhook - ERROR - Error in webhook: httpx.ProxyError: 503 Service Unavailable
2026-11-17 10:05:00,000 - caccometro.bot - INFO - Update 140785498 done: command=message chat=group ms=700 attempts=1 outcome=ok
2026-11-17 10:06:00,000 - caccometro.bot - INFO - Update 140785499 done: command=/leaderboard_month chat=private ms=1800 attempts=1 outcome=ok
2026-11-17 10:07:00,000 - caccometro.bot - INFO - Update 140785500 done: command=/leaderboard_month chat=group ms=2400 attempts=1 outcome=ok
2026-11-17 11:00:00,000 - caccometro.messages - ERROR - Strange failure for @someone 42
2026-11-17 11:30:00,000 - caccometro.maps - WARNING - Map tile 6/34/23 not refreshed: using the stale copy
2026-11-17 11:31:00,000 - caccometro.maps - WARNING - Map tile 6/34/24 not refreshed: using the stale copy
2026-11-16 11:00:00,000 - caccometro.messages - ERROR - Too old
""".splitlines()
ACCESS = """\
1.2.3.4 - - [17/Nov/2026:09:00:00 +0000] "POST /webhook HTTP/1.1" 200 2 "-" "-" "1.2.3.4" response-time=0.5
1.2.3.4 - - [17/Nov/2026:09:00:20 +0000] "POST /webhook HTTP/1.1" 500 5 "-" "-" "1.2.3.4" response-time=21.5
1.2.3.4 - - [17/Nov/2026:09:30:00 +0000] "POST /webhook HTTP/1.1" 403 5 "-" "-" "1.2.3.4" response-time=0.001
1.2.3.4 - - [17/Nov/2026:09:31:00 +0000] "HEAD / HTTP/1.1" 200 0 "-" "Mozilla/5.0+(compatible; UptimeRobot/2.0)" "1.2.3.4" response-time=0.001
1.2.3.4 - - [17/Nov/2026:09:32:00 +0000] "GET /wp-login.php HTTP/1.1" 404 0 "-" "curl" "1.2.3.4" response-time=0.001
""".splitlines()
SERVER = """\
2026-11-17 08:40:08 WSGI app 0 (mountpoint='') ready in 8 seconds on interpreter 0x5f pid: 1 (default app)
2026-11-17 08:40:08 spawned uWSGI worker 1 (pid: 5, cores: 1)
2026-11-15 08:40:08 WSGI app 0 (mountpoint='') ready in 8 seconds on interpreter 0x5f pid: 1 (default app)
""".splitlines()
ERRORS = ["2026-11-17 09:00:00,123: Something the bot printed", "  continuation without a time"]


def summary(**kwargs):
    return ls.summarize(BOT, ACCESS, SINCE, UNTIL, error_lines=ERRORS, server_lines=SERVER, **kwargs)


def test_counts_commands_and_new_kinds():
    text, new, reasons = summary()
    assert new == ["Strange failure for @U N", "Map tile N/N/N not refreshed: using the stale copy"]
    assert "Update ricevuti: 4 (privati 1, gruppi 3)" in text
    assert "Tentativi ripetuti verso Telegram: 1" in text
    assert "Risposte perse (tentativi finiti): 1" in text
    assert "Chiamate rifiutate dal webhook: 1" in text
    assert "Update piu' lento: 21.5 s alle 17/11 10:00" in text  # UTC access log shown in Rome time
    assert "  message: 2, 10.3 s, 19.9 s" in text
    assert "  /leaderboard_month: 2, 2.1 s, 2.4 s" in text
    assert "Too old" not in text and "HTTP 500" not in text  # the 500 is the one answering "Error in webhook"
    assert text.count("<-- NUOVO") == 2
    assert "  17/11 11:00 Strange failure for @someone 42" in text  # exceptions with their time
    assert "Riavvii dell'app: 1, 17/11 09:40" in text
    assert "Righe nell'error log del server: 1" in text
    assert "1 x GET /wp-login.php 404" in text and "HEAD /" not in text
    assert reasons == ["Risposte perse: 1",
                       "Errore nuovo: Strange failure for @U N",
                       "Errore nuovo: Map tile N/N/N not refreshed: using the stale copy",
                       "Update lento: message 19.9 s alle 17/11 10:00",
                       "Righe nell'error log del server: 1"]


def test_seen_kinds_are_not_new_again_and_unexplained_500_is():
    seen = {"Strange failure for @U N", "Map tile N/N/N not refreshed: using the stale copy"}
    assert summary(seen=seen)[1] == []
    only_access = ls.summarize([], ACCESS, SINCE, UNTIL)
    assert only_access[1] == ["HTTP 500 on POST /webhook"]


def test_a_repeated_error_is_an_alert_even_when_seen_but_a_repeated_warning_is_not():
    bot = BOT + ["2026-11-17 12:00:00,000 - caccometro.messages - ERROR - Strange failure for @other 7"]
    seen = {"Strange failure for @U N", "Map tile N/N/N not refreshed: using the stale copy"}
    reasons = ls.summarize(bot, [], SINCE, UNTIL, seen)[2]
    assert "Errore ripetuto 2 volte: Strange failure for @U N" in reasons
    assert not any("Map tile" in r for r in reasons)


def test_a_quiet_night_has_no_reasons():
    text, new, reasons = ls.summarize(BOT[6:9], [], SINCE, UNTIL)
    assert (new, reasons) == ([], [])
    assert "Eccezioni: nessuna" in text and "Riavvii dell'app: 0" in text
