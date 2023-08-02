from collections.abc import Generator
from typing import Any

import pytest
from loguru import logger
from pytest import LogCaptureFixture

from pyDataService import DataService
from pyDataService.data_service.callback_manager import CallbackManager


@pytest.fixture
def caplog(caplog: LogCaptureFixture) -> Generator[LogCaptureFixture, Any, None]:
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)


def emit(self: Any, parent_path: str, name: str, value: Any) -> None:
    if isinstance(value, DataService):
        value = value.serialize()

    print(f"{parent_path}.{name} = {value}")


CallbackManager.emit_notification = emit  # type: ignore
