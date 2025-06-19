import asyncio
import logging
import logging.config
import sys
from collections.abc import Callable
from copy import copy
from typing import ClassVar, Literal, TextIO

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
    "filters": {
        "only_pydase_server": {
            "()": "pydase.utils.logging.NameFilter",
            "match": "pydase.server",
        },
        "exclude_pydase_server": {
            "()": "pydase.utils.logging.NameFilter",
            "match": "pydase.server",
            "invert": True,
        },
    },
    "handlers": {
        "stdout_handler": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["only_pydase_server"],
        },
        "stderr_handler": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "filters": ["exclude_pydase_server"],
        },
    },
    "loggers": {
        "pydase": {
            "handlers": ["stdout_handler", "stderr_handler"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "aiohttp_middlewares": {
            "handlers": ["stderr_handler"],
            "level": logging.WARNING,
            "propagate": False,
        },
        "aiohttp": {
            "handlers": ["stderr_handler"],
            "level": logging.INFO,
            "propagate": False,
        },
    },
}


class NameFilter(logging.Filter):
    """
    Logging filter that allows filtering logs based on the logger name.
    Can either include or exclude a specific logger.
    """

    def __init__(self, match: str, invert: bool = False):
        super().__init__()
        self.match = match
        self.invert = invert

    def filter(self, record: logging.LogRecord) -> bool:
        if self.invert:
            return not record.name.startswith(self.match)
        return record.name.startswith(self.match)


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
        if loop.is_running():
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


def configure_logging_with_pydase_formatter(
    name: str | None = None, level: int = logging.INFO, stream: TextIO | None = None
) -> None:
    """Configure a logger with the pydase `DefaultFormatter`.

    This sets up a `StreamHandler` with the custom `DefaultFormatter`, which includes
    timestamp, log level with color (if supported), logger name, function, and line
    number. It can be used to configure the root logger or any named logger.

    Args:
        name: The name of the logger to configure. If None, the root logger is used.
        level: The logging level to set on the logger (e.g., logging.DEBUG,
            logging.INFO). Defaults to logging.INFO.
        stream: The output stream for the log messages (e.g., sys.stdout or sys.stderr).
            If None, defaults to sys.stderr.

    Example:
        Configure logging in your service:

        ```python
        import sys
        from pydase.utils.logging import configure_logging_with_pydase_formatter

        configure_logging_with_pydase_formatter(
            name="my_service",      # Use the package/module name or None for the root logger
            level=logging.DEBUG,    # Set the desired logging level (defaults to INFO)
            stream=sys.stdout       # Set the output stream (stderr by default)
        )
        ```

    Notes:
        - This function adds a new handler each time it's called.
          Use carefully to avoid duplicate logs.
        - Colors are enabled if the stream supports TTY (e.g., in terminal).
    """  # noqa: E501

    logger = logging.getLogger(name=name)
    handler = logging.StreamHandler(stream=stream)
    formatter = DefaultFormatter(
        fmt="%(asctime)s.%(msecs)03d | %(levelprefix)s | "
        "%(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
