"""The log file is bounded: it must not grow forever on a disk with a small quota."""
import logging
from logging.handlers import RotatingFileHandler

import caccometro


def test_the_log_file_handler_rotates():
    assert isinstance(caccometro.file_handler, RotatingFileHandler)


def test_the_log_stays_within_a_few_megabytes():
    handler = caccometro.file_handler
    assert handler.maxBytes == caccometro.LOG_MAX_BYTES == 1_000_000
    assert handler.backupCount == caccometro.LOG_BACKUPS == 3
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
