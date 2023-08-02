from collections.abc import Generator
from typing import Any, cast

import pytest
from loguru import logger
from pytest import LogCaptureFixture

from pyDataInterface import DataService
from pyDataInterface.data_service.callback_manager import CallbackManager


@pytest.fixture
def caplog(caplog: LogCaptureFixture) -> Generator[LogCaptureFixture, Any, None]:
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)


def emit(self: Any, parent_path: str, name: str, value: Any) -> None:
    if isinstance(value, DataService):
        value = value.serialize()

    print(f"{parent_path}.{name} = {value}")


cast(CallbackManager, DataService._callback_manager).emit_notification = emit  # type: ignore
