"""The log file is bounded: it must not grow forever on a disk with a small quota."""
import logging
import os
import subprocess
import sys
from logging.handlers import RotatingFileHandler

import pytest

from caccometro import bot, config


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
    handlers = bot._log_handlers("WEBHOOK")
    assert handlers == [bot.file_handler]


def test_webhook_mode_stops_the_bot_records_before_the_root_logger(tmp_path, monkeypatch):
    """A handler added to the root logger later (the hosting does it) must not get the records of the bot."""
    app_logger = logging.getLogger("caccometro")
    monkeypatch.setattr(app_logger, "handlers", [])
    monkeypatch.setattr(app_logger, "propagate", True)
    bot._keep_app_log_out_of_the_root_logger("WEBHOOK")
    seen = []
    hosting = logging.Handler()
    hosting.emit = seen.append
    root = logging.getLogger()
    root.addHandler(hosting)
    try:
        logging.getLogger("caccometro.webhook").info("bot record")
        logging.getLogger("telegram.ext").warning("library record")
    finally:
        root.removeHandler(hosting)
    assert [r.getMessage() for r in seen] == ["library record"]
    assert app_logger.handlers == [bot.file_handler]


def test_polling_mode_keeps_the_logger_as_it_is(monkeypatch):
    app_logger = logging.getLogger("caccometro")
    monkeypatch.setattr(app_logger, "handlers", [])
    monkeypatch.setattr(app_logger, "propagate", True)
    bot._keep_app_log_out_of_the_root_logger("POLLING")
    assert app_logger.handlers == [] and app_logger.propagate


def test_polling_mode_also_prints_to_the_console():
    handlers = bot._log_handlers("POLLING")
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


def test_database_and_log_paths_do_not_depend_on_the_working_directory(tmp_path):
    code = ("import os; os.environ.pop('LOG_FILE', None); "
            "from caccometro import bot, database; print(database.DB_FOLDER); print(bot.file_handler.baseFilename)")
    env = {**os.environ, "BOT_TOKEN": "123:test", "PYTHONPATH": str(config.PROJECT_DIR)}
    out = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, capture_output=True, text=True, check=True)
    db_folder, log_file = out.stdout.split()
    assert db_folder == str(config.PROJECT_DIR / "db")
    assert log_file == str(config.PROJECT_DIR / "caccometro.log")
