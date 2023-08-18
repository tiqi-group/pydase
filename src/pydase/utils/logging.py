import logging
import sys
from types import FrameType
from typing import Optional

import loguru
import rpyc
from uvicorn.config import LOGGING_CONFIG

import pydase.config

ALLOWED_LOG_LEVELS = ["DEBUG", "INFO", "ERROR"]


# from: https://github.com/Delgan/loguru section
# "Entirely compatible with standard logging"
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Ignore "asyncio.CancelledError" raised by uvicorn
        if record.name == "uvicorn.error" and "CancelledError" in record.msg:
            return

        # Get corresponding Loguru level if it exists.
        level: int | str
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame: Optional[FrameType] = sys._getframe(6)
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        try:
            msg = record.getMessage()
        except TypeError:
            # A `TypeError` is raised when the `msg` string expects more arguments
            # than are provided by `args`. This can happen when intercepting log
            # messages with a certain format, like
            # >    logger.debug("call: %s%r", method_name, *args)  # in tiqi_rpc
            # where `*args` unpacks a sequence of values that should replace
            # placeholders in the string.
            msg = record.msg % (record.args[0], record.args[2:])  # type: ignore

        loguru.logger.opt(depth=depth, exception=record.exc_info).log(level, msg)


def setup_logging(level: Optional[str] = None) -> None:
    loguru.logger.debug("Configuring service logging.")

    if pydase.config.OperationMode().environment == "development":
        log_level = "DEBUG"
    else:
        log_level = "INFO"

    if level is not None and level in ALLOWED_LOG_LEVELS:
        log_level = level

    loguru.logger.remove()
    loguru.logger.add(sys.stderr, level=log_level)

    # set up the rpyc logger *before* adding the InterceptHandler to the logging module
    rpyc.setup_logger(quiet=True)  # type: ignore

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.INFO)

    # overwriting the uvicorn logging config to use the loguru intercept handler
    LOGGING_CONFIG["handlers"] = {
        "default": {
            "()": InterceptHandler,
            "formatter": "default",
        },
        "access": {
            "()": InterceptHandler,
            "formatter": "access",
        },
    }
