from collections.abc import Generator
from typing import Any

from pydase import DataService
from pydase.data_service.callback_manager import CallbackManager


def emit(self: Any, parent_path: str, name: str, value: Any) -> None:
    if isinstance(value, DataService):
        value = value.serialize()

    print(f"{parent_path}.{name} = {value}")


CallbackManager.emit_notification = emit  # type: ignore
