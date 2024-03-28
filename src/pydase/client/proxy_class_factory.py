import logging
from collections.abc import Callable
from copy import copy
from typing import Any, cast

import socketio  # type: ignore

import pydase
import pydase.components
import pydase.observer_pattern.observer
from pydase.utils.helpers import is_property_attribute
from pydase.utils.serialization.deserializer import Deserializer, loads
from pydase.utils.serialization.serializer import (
    SerializedMethod,
    SerializedObject,
    dump,
)

logger = logging.getLogger(__name__)


class ProxyClassMixin:
    _sio: socketio.Client

    def __setattr__(self, key: str, value: Any) -> None:
        # prevent overriding of proxy attributes
        if (
            not is_property_attribute(self, key)
            and hasattr(self, key)
            and isinstance(getattr(self, key), ProxyBaseClass)
        ):
            raise AttributeError(f"{key} is read-only and cannot be overridden.")

        super().__setattr__(key, value)


class ProxyBaseClass(pydase.DataService, ProxyClassMixin):
    pass


class ProxyConnection(pydase.components.DeviceConnection, ProxyClassMixin):
    def __init__(self) -> None:
        super().__init__()
        self._initialised = False
        self._reconnection_wait_time = 1

    @property
    def connected(self) -> bool:
        return self._sio.connected


class ProxyClassFactory:
    def __init__(self, sio_client: socketio.Client) -> None:
        self.sio_client = sio_client

    def create_proxy(self, data: SerializedObject) -> ProxyConnection:
        proxy_class = self._deserialize_component_type(data, ProxyConnection)
        proxy_class._sio = self.sio_client
        proxy_class._initialised = True
        return proxy_class  # type: ignore

    def _deserialize(self, serialized_object: SerializedObject) -> Any:
        type_handler: dict[str | None, None | Callable[..., Any]] = {
            None: None,
            "int": self._create_attr_property,
            "float": self._create_attr_property,
            "bool": self._create_attr_property,
            "str": self._create_attr_property,
            "NoneType": self._create_attr_property,
            "Quantity": self._create_attr_property,
            "Enum": self._create_attr_property,
            "ColouredEnum": self._create_attr_property,
            "list": loads,
            "dict": loads,
            "Exception": loads,
        }

        # First go through handled types (as ColouredEnum is also within the components)
        handler = type_handler.get(serialized_object["type"])
        if handler:
            return handler(serialized_object)

        # Custom types like Components or DataService classes
        component_class = Deserializer.get_component_class(serialized_object["type"])
        if component_class:
            proxy_class = self._deserialize_component_type(
                serialized_object, component_class
            )
            proxy_class._sio = self.sio_client
            proxy_class._initialised = True
            return proxy_class
        return None

    def _deserialize_method(
        self, serialized_object: SerializedMethod
    ) -> Callable[..., Any]:
        def method_proxy(self: ProxyBaseClass, *args: Any, **kwargs: Any) -> Any:
            serialized_response = cast(
                dict[str, Any],
                self._sio.call(
                    "trigger_method",
                    {
                        "access_path": serialized_object["full_access_path"],
                        "args": dump(list(args)),
                        "kwargs": dump(kwargs),
                    },
                ),
            )
            return loads(serialized_response)  # type: ignore

        return method_proxy

    def _deserialize_component_type(
        self, serialized_object: SerializedObject, base_class: type
    ) -> pydase.DataService:
        def add_prefix_to_last_path_element(s: str, prefix: str) -> str:
            parts = s.split(".")
            parts[-1] = f"{prefix}_{parts[-1]}"
            return ".".join(parts)

        def create_proxy_class(serialized_object: SerializedObject) -> type:
            class_bases = (
                ProxyBaseClass,
                base_class,
            )
            class_attrs: dict[str, Any] = {}

            # Process and add properties based on the serialized object
            for key, value in cast(
                dict[str, SerializedObject], serialized_object["value"]
            ).items():
                if value["type"] == "method":
                    if value["async"] is True:
                        start_method = copy(value)
                        start_method["full_access_path"] = (
                            add_prefix_to_last_path_element(
                                start_method["full_access_path"], "start"
                            )
                        )
                        stop_method = copy(value)
                        stop_method["full_access_path"] = (
                            add_prefix_to_last_path_element(
                                stop_method["full_access_path"], "stop"
                            )
                        )
                        class_attrs[f"start_{key}"] = self._deserialize_method(
                            start_method
                        )
                        class_attrs[f"stop_{key}"] = self._deserialize_method(
                            stop_method
                        )
                    else:
                        class_attrs[key] = self._deserialize_method(value)
                else:
                    class_attrs[key] = self._deserialize(value)

            # Create the dynamic class with the given name and attributes
            return type(serialized_object["name"], class_bases, class_attrs)  # type: ignore

        return create_proxy_class(serialized_object)()

    def _create_attr_property(self, serialized_attr: SerializedObject) -> property:
        def get(self: ProxyBaseClass) -> Any:  # type: ignore
            return loads(
                cast(
                    SerializedObject,
                    self._sio.call("get_value", serialized_attr["full_access_path"]),
                )
            )

        get.__doc__ = serialized_attr["doc"]

        def set(self: ProxyBaseClass, value: Any) -> None:  # type: ignore
            result = cast(
                SerializedObject | None,
                self._sio.call(
                    "update_value",
                    {
                        "access_path": serialized_attr["full_access_path"],
                        "value": dump(value),
                    },
                ),
            )
            if result is not None:
                loads(result)

        if serialized_attr["readonly"]:
            return property(get)
        return property(get, set)
