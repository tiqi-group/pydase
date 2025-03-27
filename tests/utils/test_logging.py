import logging

import pytest
from pydase.utils.logging import configure_logging_with_pydase_formatter


def test_log_error(caplog: pytest.LogCaptureFixture) -> None:
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


def test_log_warning(caplog: pytest.LogCaptureFixture) -> None:
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


def test_log_debug(caplog: pytest.LogCaptureFixture) -> None:
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


def test_log_info(caplog: pytest.LogCaptureFixture) -> None:
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


def test_before_configuring_root_logger(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger(__name__)
    logger.info("Hello world")

    assert "Hello world" not in caplog.text


def test_configure_root_logger(caplog: pytest.LogCaptureFixture) -> None:
    configure_logging_with_pydase_formatter()
    logger = logging.getLogger(__name__)
    logger.info("Hello world")

    assert (
        "INFO     tests.utils.test_logging:test_logging.py:83 Hello world"
        in caplog.text
    )
