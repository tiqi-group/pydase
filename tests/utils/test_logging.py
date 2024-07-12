import logging

from pytest import LogCaptureFixture


def test_log_error(caplog: LogCaptureFixture):
    logger = logging.getLogger("pydase")
    logger.setLevel(logging.ERROR)

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
    logger = logging.getLogger("pydase")
    logger.setLevel(logging.WARNING)

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
    logger = logging.getLogger("pydase")
    logger.setLevel(logging.DEBUG)

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
    logger = logging.getLogger("pydase")
    logger.setLevel(logging.INFO)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Now, check that the message is in the log records.
    assert "This is a debug message" not in caplog.text
    assert "This is an info message" in caplog.text
    assert "This is a warning message" in caplog.text
    assert "This is an error message" in caplog.text
