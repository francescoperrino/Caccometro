"""tools/log_summary.py: counts, known and new kinds of errors."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import log_summary as ls  # noqa: E402

SINCE, UNTIL = datetime(2026, 11, 17, 0, 0), datetime(2026, 11, 18, 0, 0)
BOT = """\
2026-11-17 10:00:00,100 - caccometro.webhook - INFO - Webhook received...
2026-11-17 10:00:01,000 - caccometro.bot - WARNING - Telegram request failed (httpx.ProxyError: 503 Service Unavailable), new attempt in 1 s
2026-11-17 10:00:20,000 - caccometro.bot - ERROR - Update "140785497" caused error "httpx.ProxyError: 503 Service Unavailable"
Traceback (most recent call last):
2026-11-17 10:00:21,000 - caccometro.webhook - ERROR - Error in webhook: httpx.ProxyError: 503 Service Unavailable
2026-11-17 11:00:00,000 - caccometro.messages - ERROR - Strange failure for @someone 42
2026-11-16 11:00:00,000 - caccometro.messages - ERROR - Too old
""".splitlines()
ACCESS = """\
1.2.3.4 - - [17/Nov/2026:09:00:00 +0000] "POST /webhook HTTP/1.1" 200 2 "-" "-" "1.2.3.4" response-time=0.5
1.2.3.4 - - [17/Nov/2026:09:00:20 +0000] "POST /webhook HTTP/1.1" 500 5 "-" "-" "1.2.3.4" response-time=21.5
1.2.3.4 - - [17/Nov/2026:09:30:00 +0000] "POST /webhook HTTP/1.1" 403 5 "-" "-" "1.2.3.4" response-time=0.001
1.2.3.4 - - [17/Nov/2026:09:31:00 +0000] "HEAD / HTTP/1.1" 200 0 "-" "-" "1.2.3.4" response-time=9.9
""".splitlines()


def test_counts_and_new_kinds():
    text, new = ls.summarize(BOT, ACCESS, SINCE, UNTIL)
    assert new == ["Strange failure for @U N"]
    assert "Update ricevuti: 1" in text
    assert "Tentativi ripetuti verso Telegram: 1" in text
    assert "Risposte perse (tentativi finiti): 1" in text
    assert "Chiamate rifiutate dal webhook: 1" in text
    assert "Update piu' lento: 21.5 s alle 17/11 10:00" in text  # UTC access log shown in Rome time
    assert "Too old" not in text and "HTTP 500" not in text  # the 500 is the one answering "Error in webhook"
    assert text.count("<-- NUOVO") == 1


def test_seen_kinds_are_not_new_again_and_unexplained_500_is():
    assert ls.summarize(BOT, ACCESS, SINCE, UNTIL, seen={"Strange failure for @U N"})[1] == []
    only_access = ls.summarize([], ACCESS, SINCE, UNTIL)
    assert only_access[1] == ["HTTP 500 on POST /webhook"]
