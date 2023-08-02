from collections.abc import Generator
from typing import Any

import pytest
from loguru import logger
from pytest import LogCaptureFixture

from pyDataInterface import DataService


@pytest.fixture
def caplog(caplog: LogCaptureFixture) -> Generator[LogCaptureFixture, Any, None]:
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)


def emit(self: Any, parent_path: str, name: str, value: Any) -> None:
    if isinstance(value, DataService):
        value = value.serialize()

    print(f"{parent_path}.{name} = {value}")


DataService._emit_notification = emit  # type: ignore
