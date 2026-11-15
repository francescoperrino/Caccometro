"""The log file is bounded: it must not grow forever on a disk with a small quota."""
import logging
import os
from logging.handlers import RotatingFileHandler

import pytest

from caccometro import bot


def test_the_log_file_handler_rotates():
    assert isinstance(bot.file_handler, RotatingFileHandler)


def test_the_log_stays_within_a_few_megabytes():
    handler = bot.file_handler
    assert handler.maxBytes == bot.LOG_MAX_BYTES == 1_000_000
    assert handler.backupCount == bot.LOG_BACKUPS == 3
    assert handler.maxBytes * (handler.backupCount + 1) <= 5_000_000


def test_rotation_really_happens(tmp_path):
    folder = tmp_path / "logs"
    folder.mkdir()
    handler = RotatingFileHandler(folder / "test.log", maxBytes=2_000, backupCount=2, encoding="utf-8")
    logger = logging.getLogger("rotation_test")
    logger.propagate = False
    logger.addHandler(handler)
    try:
        for i in range(200):
            logger.warning("line %d %s", i, "x" * 50)
    finally:
        logger.removeHandler(handler)
        handler.close()
    assert sorted(p.name for p in folder.iterdir()) == ["test.log", "test.log.1", "test.log.2"]
    assert all(p.stat().st_size <= 2_100 for p in folder.iterdir())


def test_the_tests_never_write_to_the_real_log():
    assert bot.file_handler.baseFilename != os.path.abspath("caccometro.log")


def test_webhook_mode_writes_the_log_only_to_the_file():
    """The console is the web server error log there: one copy is enough."""
    handlers = bot.log_handlers("WEBHOOK")
    assert handlers == [bot.file_handler]


def test_polling_mode_also_prints_to_the_console():
    handlers = bot.log_handlers("POLLING")
    assert handlers[0] is bot.file_handler
    assert type(handlers[1]) is logging.StreamHandler


@pytest.mark.parametrize("utc_seconds,rome_time", [
    (1782907200, "2026-07-01 14:00:00"),   # 12:00 UTC in summer: UTC+2
    (1796126400, "2026-12-01 13:00:00"),   # 12:00 UTC in winter: UTC+1
])
def test_log_times_are_in_italian_time(utc_seconds, rome_time):
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)
    record.created = utc_seconds
    assert logging.Formatter("%(asctime)s").format(record).startswith(rome_time)
