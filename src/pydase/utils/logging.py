import asyncio
import logging
import logging.config
import sys
from copy import copy

import socketio  # type: ignore[import-untyped]
import uvicorn.config
import uvicorn.logging

import pydase.config

logger = logging.getLogger(__name__)

if pydase.config.OperationMode().environment == "development":
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "pydase.utils.logging.DefaultFormatter",
            "fmt": "%(asctime)s.%(msecs)03d | %(levelprefix)s | "
            "%(name)s:%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "pydase": {"handlers": ["default"], "level": LOG_LEVEL, "propagate": False},
    },
}


class DefaultFormatter(uvicorn.logging.ColourizedFormatter):
    """
    A custom log formatter class that:

    * Outputs the LOG_LEVEL with an appropriate color.
    * If a log call includes an `extras={"color_message": ...}` it will be used
      for formatting the output, instead of the plain text message.
    """

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa: N802
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        seperator = " " * (8 - len(recordcopy.levelname))
        if self.use_colors:
            levelname = self.color_level_name(levelname, recordcopy.levelno)
            if "color_message" in recordcopy.__dict__:
                recordcopy.msg = recordcopy.__dict__["color_message"]
                recordcopy.__dict__["message"] = recordcopy.getMessage()
        recordcopy.__dict__["levelprefix"] = levelname + seperator
        return logging.Formatter.formatMessage(self, recordcopy)

    def should_use_colors(self) -> bool:
        return sys.stderr.isatty()


class SocketIOHandler(logging.Handler):
    """
    Custom logging handler that emits ERROR and CRITICAL log records to a Socket.IO
    server, allowing for real-time logging in applications that use Socket.IO for
    communication.
    """

    def __init__(self, sio: socketio.AsyncServer) -> None:
        super().__init__(logging.ERROR)
        self._sio = sio

    def format(self, record: logging.LogRecord) -> str:
        return f"{record.name}:{record.funcName}:{record.lineno} - {record.message}"

    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)

        loop = asyncio.get_event_loop()
        loop.create_task(
            self._sio.emit(
                "log",
                {
                    "levelname": record.levelname,
                    "message": log_entry,
                },
            )
        )


def setup_logging() -> None:
    """
    Configures the logging settings for the application.

    This function sets up logging with specific formatting and colorization of log
    messages. The log level is determined based on the application's operation mode. By
    default, in a development environment, the log level is set to DEBUG, whereas in
    other environments, it is set to INFO.
    """

    logger.debug("Configuring pydase logging.")

    logging.config.dictConfig(LOGGING_CONFIG)

    # configuring uvicorn logger
    uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["fmt"] = (
        "%(asctime)s.%(msecs)03d | %(levelprefix)s %(message)s"
    )
    uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["datefmt"] = (
        "%Y-%m-%d %H:%M:%S"
    )
    uvicorn.config.LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
        "%(asctime)s.%(msecs)03d | %(levelprefix)s %(client_addr)s "
        '- "%(request_line)s" %(status_code)s'
    )
    uvicorn.config.LOGGING_CONFIG["formatters"]["access"]["datefmt"] = (
        "%Y-%m-%d %H:%M:%S"
    )
