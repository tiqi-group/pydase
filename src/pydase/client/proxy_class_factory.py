import logging
from copy import copy
from typing import TYPE_CHECKING, Any, cast

import socketio  # type: ignore

import pydase
from pydase.utils.serialization.deserializer import Deserializer, loads
from pydase.utils.serialization.serializer import (
    SerializedMethod,
    SerializedObject,
    dump,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    import pydase.components

    class ProxyClass(pydase.DataService):
        _sio: socketio.Client


logger = logging.getLogger(__name__)


class ProxyClassFactory:
    def __init__(self, sio_client: socketio.Client) -> None:
        self.sio_client = sio_client

    def create_proxy(self, data: SerializedObject) -> "ProxyClass":
        proxy: "ProxyClass" = self._deserialize(data)
        return proxy

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
            return proxy_class
        return None

    def _deserialize_method(self, serialized_object: SerializedMethod) -> Any:
        def method_proxy(self: "ProxyClass", *args: Any, **kwargs: Any) -> Any:
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
    ) -> Any:
        def add_prefix_to_last_path_element(s: str, prefix: str) -> str:
            parts = s.split(".")
            parts[-1] = f"{prefix}_{parts[-1]}"
            return ".".join(parts)

        def create_proxy_class(serialized_object: SerializedObject) -> type:
            class_bases = (base_class,)
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
        def get(self: "ProxyClass") -> Any:  # type: ignore
            return loads(
                cast(
                    SerializedObject,
                    self._sio.call("get_value", serialized_attr["full_access_path"]),
                )
            )

        get.__doc__ = serialized_attr["doc"]

        def set(self: "ProxyClass", value: Any) -> None:  # type: ignore
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
