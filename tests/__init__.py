from typing import Any

from pyDataInterface import DataService


def emit(self: Any, parent_path: str, name: str, value: Any) -> None:
    if isinstance(value, DataService):
        value = value.serialize()

    print(f"{parent_path}.{name} = {value}")


DataService._emit_notification = emit  # type: ignore
