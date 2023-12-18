import logging

from pydase.utils.logging import setup_logging
from pytest import LogCaptureFixture


def test_log_error(caplog: LogCaptureFixture):
    setup_logging("ERROR")
    logger = logging.getLogger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Check the log records as well as the level.
    assert "This is a debug message" not in caplog.text
    assert "This is an info message" not in caplog.text
    assert "This is a warning message" not in caplog.text
    assert "This is an error message" in caplog.text
    assert any(record.levelname == "ERROR" for record in caplog.records)


def test_log_warning(caplog: LogCaptureFixture):
    setup_logging("WARNING")
    logger = logging.getLogger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Check the log records as well as the level.
    assert "This is a debug message" not in caplog.text
    assert "This is an info message" not in caplog.text
    assert "This is a warning message" in caplog.text
    assert "This is an error message" in caplog.text
    assert any(record.levelname == "ERROR" for record in caplog.records)


def test_log_debug(caplog: LogCaptureFixture):
    setup_logging("DEBUG")
    logger = (
        logging.getLogger()
    )  # Get the root logger or replace with the appropriate logger.
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Now, check that the message is in the log records.
    assert "This is a debug message" in caplog.text
    assert "This is an info message" in caplog.text
    assert "This is a warning message" in caplog.text
    assert "This is an error message" in caplog.text


def test_log_info(caplog: LogCaptureFixture):
    setup_logging("INFO")
    logger = (
        logging.getLogger()
    )  # Get the root logger or replace with the appropriate logger.
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Now, check that the message is in the log records.
    assert "This is a debug message" not in caplog.text
    assert "This is an info message" in caplog.text
    assert "This is a warning message" in caplog.text
    assert "This is an error message" in caplog.text
