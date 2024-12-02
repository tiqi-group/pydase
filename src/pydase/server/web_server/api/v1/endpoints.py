from typing import TYPE_CHECKING, Any

import pydase.utils.serialization.deserializer
import pydase.utils.serialization.serializer
from pydase.data_service.state_manager import StateManager
from pydase.server.web_server.sio_setup import TriggerMethodDict, UpdateDict
from pydase.utils.helpers import get_object_attr_from_path
from pydase.utils.serialization.types import SerializedObject

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

loads = pydase.utils.serialization.deserializer.loads
Serializer = pydase.utils.serialization.serializer.Serializer


def update_value(state_manager: StateManager, data: UpdateDict) -> None:
    path = data["access_path"]

    state_manager.set_service_attribute_value_by_path(
        path=path, serialized_value=data["value"]
    )


def get_value(state_manager: StateManager, access_path: str) -> SerializedObject:
    return Serializer.serialize_object(
        get_object_attr_from_path(state_manager.service, access_path),
        access_path=access_path,
    )


def trigger_method(state_manager: StateManager, data: TriggerMethodDict) -> Any:
    method = get_object_attr_from_path(state_manager.service, data["access_path"])

    serialized_args = data.get("args", None)
    args = loads(serialized_args) if serialized_args else []

    serialized_kwargs = data.get("kwargs", None)
    kwargs: dict[str, Any] = loads(serialized_kwargs) if serialized_kwargs else {}

    return Serializer.serialize_object(method(*args, **kwargs))


async def trigger_async_method(
    state_manager: StateManager, data: TriggerMethodDict
) -> Any:
    method: Callable[..., Awaitable[Any]] = get_object_attr_from_path(
        state_manager.service, data["access_path"]
    )

    serialized_args = data.get("args", None)
    args = loads(serialized_args) if serialized_args else []

    serialized_kwargs = data.get("kwargs", None)
    kwargs: dict[str, Any] = loads(serialized_kwargs) if serialized_kwargs else {}

    return Serializer.serialize_object(await method(*args, **kwargs))
