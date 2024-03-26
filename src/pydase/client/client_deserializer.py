import enum
import logging
from typing import Any, cast

import socketio  # type: ignore

from pydase.utils.deserializer import Deserializer, loads
from pydase.utils.serializer import SerializedObject, dump

logger = logging.getLogger(__name__)


class ClientDeserializer(Deserializer):
    _sio: socketio.Client

    @classmethod
    def deserialize_method(cls, serialized_object: SerializedObject) -> Any:
        def method_proxy(self: Any, *args: Any, **kwargs: Any) -> Any:
            serialized_response = cast(
                dict[str, Any],
                cls._sio.call(
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

    @classmethod
    def deserialize_primitive(cls, serialized_object: SerializedObject) -> Any:
        return cls.create_attr_property(serialized_object)

    @classmethod
    def deserialize_quantity(cls, serialized_object: SerializedObject) -> Any:
        return cls.create_attr_property(serialized_object)

    @classmethod
    def deserialize_enum(
        cls,
        serialized_object: SerializedObject,
        enum_class: type[enum.Enum] = enum.Enum,
    ) -> Any:
        return cls.create_attr_property(serialized_object)

    @classmethod
    def deserialize_component_type(
        cls, serialized_object: SerializedObject, base_class: type
    ) -> Any:
        def create_proxy_class(serialized_object: SerializedObject) -> type:
            class_bases = (base_class,)
            class_attrs: dict[str, Any] = {"_sio": cls._sio}

            # Process and add properties based on the serialized object
            for key, value in cast(
                dict[str, SerializedObject], serialized_object["value"]
            ).items():
                class_attrs[key] = cls.deserialize(value)

            # Create the dynamic class with the given name and attributes
            return type(serialized_object["name"], class_bases, class_attrs)  # type: ignore

        return create_proxy_class(serialized_object)()

    @classmethod
    def create_attr_property(cls, serialized_attr: SerializedObject) -> property:
        def get(self) -> Any:  # type: ignore
            return loads(
                self._sio.call("get_value", serialized_attr["full_access_path"])
            )

        get.__doc__ = serialized_attr["doc"]

        def set(self, value: Any) -> None:  # type: ignore
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
