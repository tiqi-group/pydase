import enum
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, NoReturn, cast

import pydase
import pydase.components
import pydase.units as u
from pydase.utils.helpers import (
    get_component_classes,
)
from pydase.utils.serialization.types import (
    SerializedDatetime,
    SerializedException,
    SerializedObject,
)

if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


class Deserializer:
    @classmethod
    def deserialize(cls, serialized_object: SerializedObject) -> Any:
        """Deserialize `serialized_object` (a `dict`) to a Python object."""
        type_handler: dict[str | None, None | Callable[..., Any]] = {
            None: None,
            "int": cls.deserialize_primitive,
            "float": cls.deserialize_primitive,
            "bool": cls.deserialize_primitive,
            "str": cls.deserialize_primitive,
            "NoneType": cls.deserialize_primitive,
            "Quantity": cls.deserialize_quantity,
            "Enum": cls.deserialize_enum,
            "ColouredEnum": lambda serialized_object: cls.deserialize_enum(
                serialized_object, enum_class=pydase.components.ColouredEnum
            ),
            "list": cls.deserialize_list,
            "dict": cls.deserialize_dict,
            "method": cls.deserialize_method,
            "Exception": cls.deserialize_exception,
            "datetime": cls.deserialize_datetime,
        }

        # First go through handled types (as ColouredEnum is also within the components)
        handler = type_handler.get(serialized_object["type"])
        if handler:
            return handler(serialized_object)

        # Custom types like Components or DataService classes
        service_base_class = cls.get_service_base_class(serialized_object["type"])
        if service_base_class:
            return cls.deserialize_data_service(serialized_object, service_base_class)

        return None

    @classmethod
    def deserialize_primitive(cls, serialized_object: SerializedObject) -> Any:
        if serialized_object["type"] == "float":
            return float(serialized_object["value"])
        return serialized_object["value"]

    @classmethod
    def deserialize_quantity(cls, serialized_object: SerializedObject) -> Any:
        return u.convert_to_quantity(serialized_object["value"])  # type: ignore

    @classmethod
    def deserialize_datetime(cls, serialized_object: SerializedDatetime) -> datetime:
        return datetime.fromisoformat(serialized_object["value"])

    @classmethod
    def deserialize_enum(
        cls,
        serialized_object: SerializedObject,
        enum_class: type[enum.Enum] = enum.Enum,
    ) -> Any:
        return enum_class(serialized_object["name"], serialized_object["enum"])[  # type: ignore
            serialized_object["value"]
        ]

    @classmethod
    def deserialize_list(cls, serialized_object: SerializedObject) -> Any:
        return [
            cls.deserialize(item)
            for item in cast("list[SerializedObject]", serialized_object["value"])
        ]

    @classmethod
    def deserialize_dict(cls, serialized_object: SerializedObject) -> Any:
        return {
            key: cls.deserialize(value)
            for key, value in cast(
                "dict[str, SerializedObject]", serialized_object["value"]
            ).items()
        }

    @classmethod
    def deserialize_method(cls, serialized_object: SerializedObject) -> Any:
        return

    @classmethod
    def deserialize_exception(cls, serialized_object: SerializedException) -> NoReturn:
        import builtins

        try:
            exception = getattr(builtins, serialized_object["name"])
        except AttributeError:
            exception = type(serialized_object["name"], (Exception,), {})  # type: ignore
        raise exception(serialized_object["value"])

    @staticmethod
    def get_service_base_class(type_name: str | None) -> type | None:
        for component_class in get_component_classes():
            if type_name == component_class.__name__:
                return component_class
        if type_name in ("DataService", "Task"):
            import pydase

            return pydase.DataService
        return None

    @classmethod  # TODO: this shouldn't be a class method
    def create_attr_property(cls, serialized_attr: SerializedObject) -> property:
        attr_name = serialized_attr["full_access_path"].split(".")[-1]

        def get(self) -> Any:  # type: ignore
            return getattr(self, f"_{attr_name}")

        get.__doc__ = serialized_attr["doc"]

        def set(self, value: Any) -> None:  # type: ignore
            return setattr(self, f"_{attr_name}", value)

        if serialized_attr["readonly"]:
            return property(get)
        return property(get, set)

    @classmethod
    def deserialize_data_service(
        cls, serialized_object: SerializedObject, base_class: type
    ) -> Any:
        def create_proxy_class(serialized_object: SerializedObject) -> type:
            class_bases = (base_class,)
            class_attrs = {}

            # Process and add properties based on the serialized object
            for key, value in cast(
                "dict[str, SerializedObject]", serialized_object["value"]
            ).items():
                if value["type"] != "method":
                    class_attrs[key] = cls.create_attr_property(value)
                    # Initialize a placeholder for the attribute to avoid AttributeError
                    class_attrs[f"_{key}"] = cls.deserialize(value)

            # Create the dynamic class with the given name and attributes
            return type(serialized_object["name"], class_bases, class_attrs)  # type: ignore

        return create_proxy_class(serialized_object)()


def loads(serialized_object: SerializedObject) -> Any:
    """Deserialize `serialized_object` (a `dict`) to a Python object."""
    return Deserializer.deserialize(serialized_object)
