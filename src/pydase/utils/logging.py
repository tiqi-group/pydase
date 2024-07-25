import asyncio
import logging
import logging.config
import sys
from collections.abc import Callable
from copy import copy
from typing import ClassVar, Literal

import click
import socketio  # type: ignore[import-untyped]

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
        "aiohttp_middlewares": {
            "handlers": ["default"],
            "level": logging.WARNING,
            "propagate": False,
        },
        "aiohttp": {
            "handlers": ["default"],
            "level": logging.INFO,
            "propagate": False,
        },
    },
}


class DefaultFormatter(logging.Formatter):
    """
    A custom log formatter class that:

    * Outputs the LOG_LEVEL with an appropriate color.
    * If a log call includes an `extras={"color_message": ...}` it will be used
      for formatting the output, instead of the plain text message.
    """

    level_name_colors: ClassVar[dict[int, Callable[..., str]]] = {
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(
            str(level_name), fg="bright_red"
        ),
    }

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: bool | None = None,
    ):
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        def default(level_name: str) -> str:
            return str(level_name)

        func = self.level_name_colors.get(level_no, default)
        return func(level_name)

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
        msg = record.getMessage()
        return f"{record.name}:{record.funcName}:{record.lineno} - {msg}"

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
