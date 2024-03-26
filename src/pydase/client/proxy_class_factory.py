import logging
from typing import TYPE_CHECKING, Any, cast

import socketio  # type: ignore

import pydase
from pydase.utils.deserializer import Deserializer, loads
from pydase.utils.serializer import SerializedObject, dump

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
        proxy = self._deserialize(data)
        proxy._sio = self.sio_client
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
            "method": self._deserialize_method,
            "list": loads,
            "dict": loads,
            "Exception": loads,
        }

        # Custom types like Components or DataService classes
        component_class = Deserializer.get_component_class(serialized_object["type"])
        if component_class:
            proxy_class = self._deserialize_component_type(
                serialized_object, component_class
            )
            proxy_class._sio = self.sio_client
            return proxy_class

        handler = type_handler.get(serialized_object["type"])
        if handler:
            return handler(serialized_object)
        return None

    def _deserialize_method(self, serialized_object: SerializedObject) -> Any:
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
        def create_proxy_class(serialized_object: SerializedObject) -> type:
            class_bases = (base_class,)
            class_attrs: dict[str, Any] = {}

            # Process and add properties based on the serialized object
            for key, value in cast(
                dict[str, SerializedObject], serialized_object["value"]
            ).items():
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
            self._sio.call(
                "update_value",
                {
                    "access_path": serialized_attr["full_access_path"],
                    "value": dump(value),
                },
            )

        if serialized_attr["readonly"]:
            return property(get)
        return property(get, set)
