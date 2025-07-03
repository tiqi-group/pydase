from __future__ import annotations

import inspect
import logging
import sys
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, cast

import pydase.units as u
from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.task.task_status import TaskStatus
from pydase.utils.decorators import render_in_frontend
from pydase.utils.helpers import (
    get_attribute_doc,
    get_component_classes,
    get_data_service_class_reference,
    get_task_class,
    is_property_attribute,
    parse_full_access_path,
    parse_serialized_key,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydase.client.proxy_class import ProxyClass
    from pydase.utils.serialization.types import (
        DataServiceTypes,
        SerializedBool,
        SerializedDataService,
        SerializedDatetime,
        SerializedDict,
        SerializedEnum,
        SerializedException,
        SerializedFloat,
        SerializedInteger,
        SerializedList,
        SerializedMethod,
        SerializedNoneType,
        SerializedObject,
        SerializedQuantity,
        SerializedString,
        SignatureDict,
    )

logger = logging.getLogger(__name__)


class SerializationError(Exception):
    pass


class SerializationPathError(Exception):
    pass


class Serializer:
    """Serializes objects into
    [`SerializedObject`][pydase.utils.serialization.types.SerializedObject]
    representations.
    """

    @classmethod
    def serialize_object(cls, obj: Any, access_path: str = "") -> SerializedObject:  # noqa: C901
        """Serialize `obj` to a
        [`SerializedObject`][pydase.utils.serialization.types.SerializedObject].

        Args:
            obj:
                Object to be serialized.
            access_path:
                String corresponding to the full access path of the object. This will be
                prepended to the full_access_path in the SerializedObject entries.

        Returns:
            Dictionary representation of `obj`.
        """
        from pydase.client.client import ProxyClass

        result: SerializedObject

        if isinstance(obj, Exception):
            result = cls._serialize_exception(obj)

        elif isinstance(obj, datetime):
            result = cls._serialize_datetime(obj, access_path=access_path)

        elif isinstance(obj, ProxyClass):
            result = cls._serialize_proxy_class(obj, access_path=access_path)

        elif isinstance(obj, AbstractDataService):
            result = cls._serialize_data_service(obj, access_path=access_path)

        elif isinstance(obj, list):
            result = cls._serialize_list(obj, access_path=access_path)

        elif isinstance(obj, dict):
            result = cls._serialize_dict(obj, access_path=access_path)

        # Special handling for u.Quantity
        elif isinstance(obj, u.Quantity):
            result = cls._serialize_quantity(obj, access_path=access_path)

        # Handling for Enums
        elif isinstance(obj, Enum):
            result = cls._serialize_enum(obj, access_path=access_path)

        # Methods and coroutines
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            result = cls._serialize_method(obj, access_path=access_path)

        elif isinstance(obj, int | float | bool | str | None):
            result = cls._serialize_primitive(obj, access_path=access_path)

        try:
            return result
        except UnboundLocalError:
            raise SerializationError(
                f"Could not serialized object of type {type(obj)}."
            )

    @classmethod
    def _serialize_primitive(
        cls,
        obj: float | bool | str | None,
        access_path: str,
    ) -> (
        SerializedInteger
        | SerializedFloat
        | SerializedBool
        | SerializedString
        | SerializedNoneType
    ):
        doc = get_attribute_doc(obj)
        return {  # type: ignore
            "full_access_path": access_path,
            "doc": doc,
            "readonly": False,
            "type": type(obj).__name__,
            "value": obj,
        }

    @classmethod
    def _serialize_datetime(cls, obj: datetime, access_path: str) -> SerializedDatetime:
        return {
            "type": "datetime",
            "value": str(obj),
            "doc": None,
            "full_access_path": access_path,
            "readonly": True,
        }

    @classmethod
    def _serialize_exception(cls, obj: Exception) -> SerializedException:
        return {
            "full_access_path": "",
            "doc": None,
            "readonly": True,
            "type": "Exception",
            "value": obj.args[0] if len(obj.args) > 0 else "",
            "name": obj.__class__.__name__,
        }

    @classmethod
    def _serialize_enum(cls, obj: Enum, access_path: str = "") -> SerializedEnum:
        import pydase.components.coloured_enum

        value = obj.name
        doc = obj.__doc__
        class_name = type(obj).__name__
        if sys.version_info < (3, 11) and doc == "An enumeration.":
            doc = None
        if isinstance(obj, pydase.components.coloured_enum.ColouredEnum):
            obj_type: Literal["ColouredEnum", "Enum"] = "ColouredEnum"
        else:
            obj_type = "Enum"

        return {
            "full_access_path": access_path,
            "name": class_name,
            "type": obj_type,
            "value": value,
            "readonly": False,
            "doc": doc,
            "enum": {
                name: member.value for name, member in obj.__class__.__members__.items()
            },
        }

    @classmethod
    def _serialize_quantity(
        cls, obj: u.Quantity, access_path: str = ""
    ) -> SerializedQuantity:
        doc = get_attribute_doc(obj)
        value: u.QuantityDict = {"magnitude": obj.m, "unit": str(obj.u)}
        return {
            "full_access_path": access_path,
            "type": "Quantity",
            "value": value,
            "readonly": False,
            "doc": doc,
        }

    @classmethod
    def _serialize_dict(
        cls, obj: dict[str, Any], access_path: str = ""
    ) -> SerializedDict:
        readonly = False
        doc = get_attribute_doc(obj)
        value = {}
        for key, val in obj.items():
            value[key] = cls.serialize_object(
                val, access_path=f'{access_path}["{key}"]'
            )
        return {
            "full_access_path": access_path,
            "type": "dict",
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @classmethod
    def _serialize_list(cls, obj: list[Any], access_path: str = "") -> SerializedList:
        readonly = False
        doc = get_attribute_doc(obj)
        value = [
            cls.serialize_object(o, access_path=f"{access_path}[{i}]")
            for i, o in enumerate(obj)
        ]
        return {
            "full_access_path": access_path,
            "type": "list",
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @classmethod
    def _serialize_method(
        cls, obj: Callable[..., Any], access_path: str = ""
    ) -> SerializedMethod:
        readonly = True
        doc = get_attribute_doc(obj)
        frontend_render = render_in_frontend(obj)

        # Store parameters and their anotations in a dictionary
        sig = inspect.signature(obj)
        sig.return_annotation

        signature: SignatureDict = {"parameters": {}, "return_annotation": {}}

        for k, v in sig.parameters.items():
            default_value = cast(
                "dict[str, Any]", {} if v.default == inspect._empty else dump(v.default)
            )
            default_value.pop("full_access_path", None)
            signature["parameters"][k] = {
                "annotation": str(v.annotation),
                "default": default_value,
            }

        return {
            "full_access_path": access_path,
            "type": "method",
            "value": None,
            "readonly": readonly,
            "doc": doc,
            "async": inspect.iscoroutinefunction(obj),
            "signature": signature,
            "frontend_render": frontend_render,
        }

    @classmethod
    def _serialize_data_service(
        cls, obj: AbstractDataService, access_path: str = ""
    ) -> SerializedDataService:
        readonly = False
        doc = get_attribute_doc(obj)
        obj_type: DataServiceTypes = "DataService"
        obj_name = obj.__class__.__name__

        # Get component base class if any
        component_base_cls = next(
            (cls for cls in get_component_classes() if isinstance(obj, cls)), None
        )
        if component_base_cls:
            obj_type = component_base_cls.__name__  # type: ignore

        elif isinstance(obj, get_task_class()):
            # Check if obj is a pydase task
            obj_type = "Task"

        # Get the set of DataService class attributes
        data_service_attr_set = set(dir(get_data_service_class_reference()))
        # Get the set of the object attributes
        obj_attr_set = set(dir(obj))
        # Get the difference between the two sets
        derived_only_attr_set = obj_attr_set - data_service_attr_set

        value: dict[str, SerializedObject] = {}

        # Iterate over attributes, properties, class attributes, and methods
        for key in sorted(derived_only_attr_set):
            if key.startswith("_"):
                continue  # Skip attributes that start with underscore

            val = getattr(obj, key)

            path = f"{access_path}.{key}" if access_path else key
            serialized_object = cls.serialize_object(val, access_path=path)

            value[key] = serialized_object

            # If the DataService attribute is a property
            if is_property_attribute(obj, key):
                prop: property = getattr(obj.__class__, key)
                value[key]["readonly"] = prop.fset is None
                value[key]["doc"] = get_attribute_doc(prop)  # overwrite the doc

        return {
            "full_access_path": access_path,
            "name": obj_name,
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @classmethod
    def _serialize_proxy_class(
        cls, obj: ProxyClass, access_path: str = ""
    ) -> SerializedDataService:
        # Get serialization value from the remote service and adapt the full_access_path
        return add_prefix_to_full_access_path(obj.serialize(), access_path)


def dump(obj: Any) -> SerializedObject:
    """Serialize `obj` to a
    [`SerializedObject`][pydase.utils.serialization.types.SerializedObject].

    The [`Serializer`][pydase.utils.serialization.serializer.Serializer] is used for
    encoding.

    Args:
        obj:
            Object to be serialized.

    Returns:
        Dictionary representation of `obj`.
    """
    return Serializer.serialize_object(obj)


def set_nested_value_by_path(
    serialization_dict: dict[Any, SerializedObject], path: str, value: Any
) -> None:
    """
    Set a value in a nested dictionary structure, which conforms to the serialization
    format used by [`Serializer`][pydase.utils.serialization.serializer.Serializer],
    using a dot-notation path.

    Args:
        serialization_dict:
            The base dictionary representing data serialized with
            [`Serializer`][pydase.utils.serialization.serializer.Serializer].
        path:
            The dot-notation path (e.g., 'attr1.attr2[0].attr3') indicating where to
            set the value.
        value:
            The new value to set at the specified path.

    Note:
        If the index equals the length of the list, the function will append the
        serialized representation of the 'value' to the list.
    """

    path_parts = parse_full_access_path(path)
    current_dict: dict[Any, SerializedObject] = serialization_dict

    try:
        for path_part in path_parts[:-1]:
            next_level_serialized_object = get_container_item_by_key(
                current_dict, path_part, allow_append=False
            )
            current_dict = cast(
                "dict[Any, SerializedObject]",
                next_level_serialized_object["value"],
            )

        next_level_serialized_object = get_container_item_by_key(
            current_dict, path_parts[-1], allow_append=True
        )
    except (SerializationPathError, KeyError) as e:
        logger.exception("Error occured trying to change %a: %s", path, e)
        return

    if next_level_serialized_object["type"] == "method":  # state change of task
        next_level_serialized_object["value"] = (
            "RUNNING" if isinstance(value, TaskStatus) else None
        )
    else:
        serialized_value = Serializer.serialize_object(value, access_path=path)
        serialized_value["readonly"] = next_level_serialized_object["readonly"]

        keys_to_keep = set(serialized_value.keys())

        next_level_serialized_object.update(serialized_value)  # type: ignore

        # removes keys that are not present in the serialized new value
        for key in list(next_level_serialized_object.keys()):
            if key not in keys_to_keep:
                next_level_serialized_object.pop(key, None)  # type: ignore


def get_nested_dict_by_path(
    serialization_dict: dict[Any, SerializedObject],
    path: str,
) -> SerializedObject:
    path_parts = parse_full_access_path(path)
    current_dict: dict[Any, SerializedObject] = serialization_dict

    for path_part in path_parts[:-1]:
        next_level_serialized_object = get_container_item_by_key(
            current_dict, path_part, allow_append=False
        )
        current_dict = cast(
            "dict[Any, SerializedObject]",
            next_level_serialized_object["value"],
        )
    return get_container_item_by_key(current_dict, path_parts[-1], allow_append=False)


def create_empty_serialized_object() -> SerializedObject:
    """Create a new empty serialized object."""

    return {
        "full_access_path": "",
        "value": None,
        "type": "None",
        "doc": None,
        "readonly": False,
    }


def get_or_create_item_in_container(
    container: dict[Any, SerializedObject] | list[SerializedObject],
    key: Any,
    *,
    allow_add_key: bool,
) -> SerializedObject:
    """Ensure the key exists in the dictionary, append if necessary and allowed."""

    try:
        return container[key]
    except IndexError:
        if allow_add_key and key == len(container):
            cast("list[SerializedObject]", container).append(
                create_empty_serialized_object()
            )
            return container[key]
        raise
    except KeyError:
        if allow_add_key:
            container[key] = create_empty_serialized_object()
            return container[key]
        raise


def get_container_item_by_key(
    container: dict[Any, SerializedObject] | list[SerializedObject],
    key: str,
    *,
    allow_append: bool = False,
) -> SerializedObject:
    """
    Retrieve an item from a container specified by the passed key. Add an item to the
    container if `allow_append` is set to `True`.

    If specified keys or indexes do not exist, the function can append new elements to
    dictionaries and to lists if `allow_append` is True and the missing element is
    exactly the next sequential index (for lists).

    Args:
        container:
            The container representing serialized data.
        key:
            The key name representing the attribute in the dictionary, which may include
            direct keys or indexes (e.g., 'attr_name', '["key"]' or '[0]').
        allow_append:
            Flag to allow appending a new entry if the specified index is out of range
            by exactly one position.

    Returns:
        The dictionary or list item corresponding to the specified attribute and index.

    Raises:
        SerializationPathError:
            If the path composed of `attr_name` and any specified index is invalid, or
            leads to an IndexError or KeyError. This error is also raised if an attempt
            to access a nonexistent key or index occurs without permission to append.
    """
    processed_key = parse_serialized_key(key)

    try:
        return get_or_create_item_in_container(
            container, processed_key, allow_add_key=allow_append
        )
    except IndexError as e:
        raise SerializationPathError(f"Index '{processed_key}': {e}")
    except KeyError as e:
        raise SerializationPathError(f"Key '{processed_key}': {e}")


def get_data_paths_from_serialized_object(  # noqa: C901
    serialized_obj: SerializedObject,
    parent_path: str = "",
) -> list[str]:
    """
    Recursively extracts full access paths from a serialized object.

    Args:
        serialized_obj:
            The dictionary representing the serialization of an object. Produced by
            `pydase.utils.serializer.Serializer`.

    Returns:
        A list of strings, each representing a full access path in the serialized
            object.
    """

    paths: list[str] = []

    if isinstance(serialized_obj["value"], list):
        for index, value in enumerate(serialized_obj["value"]):
            new_path = f"{parent_path}[{index}]"
            paths.append(new_path)
            if serialized_dict_is_nested_object(value):
                paths.extend(get_data_paths_from_serialized_object(value, new_path))

    elif serialized_dict_is_nested_object(serialized_obj):
        for key, value in cast(
            "dict[str, SerializedObject]", serialized_obj["value"]
        ).items():
            # Serialized dictionaries need to have a different new_path than nested
            # classes
            if serialized_obj["type"] == "dict":
                processed_key = key
                if isinstance(key, str):
                    processed_key = f'"{key}"'
                new_path = f"{parent_path}[{processed_key}]"
            else:
                new_path = f"{parent_path}.{key}" if parent_path != "" else key

            paths.append(new_path)
            if serialized_dict_is_nested_object(value):
                paths.extend(get_data_paths_from_serialized_object(value, new_path))

    return paths


def generate_serialized_data_paths(
    data: dict[str, SerializedObject],
) -> list[str]:
    """
    Recursively extracts full access paths from a serialized DataService class instance.

    Args:
        data:
            The value of the "value" key of a serialized DataService class instance.

    Returns:
        A list of strings, each representing a full access path in the serialized
            object.
    """

    paths: list[str] = []

    for key, value in data.items():
        paths.append(key)

        if serialized_dict_is_nested_object(value):
            paths.extend(get_data_paths_from_serialized_object(value, key))
    return paths


def add_prefix_to_full_access_path(
    serialized_obj: SerializedObject, prefix: str
) -> Any:
    """Recursively adds a specified prefix to all full access paths of the serialized
    object.

    Args:
        serialized_obj:
            The serialized object to process.
        prefix:
            The prefix string to prepend to each full access path.

    Returns:
        The modified serialized object with the prefix added to all full access paths.

    Example:
        ```python
        >>> serialized_obj = {
        ...     "full_access_path": "",
        ...     "value": {
        ...         "item": {
        ...             "full_access_path": "some_item_path",
        ...             "value": 1.0
        ...         }
        ...     }
        ... }
        ...
        ... modified_data = add_prefix_to_full_access_path(serialized_obj, 'prefix')
        {"full_access_path": "prefix", "value": {"item": {"full_access_path":
        "prefix.some_item_path", "value": 1.0}}}
        ```
    """

    try:
        if serialized_obj.get("full_access_path", None) is not None:
            serialized_obj["full_access_path"] = (
                prefix + "." + serialized_obj["full_access_path"]
                if serialized_obj["full_access_path"] != ""
                else prefix
            )

        if isinstance(serialized_obj["value"], list):
            for value in serialized_obj["value"]:
                add_prefix_to_full_access_path(cast("SerializedObject", value), prefix)

        elif isinstance(serialized_obj["value"], dict):
            for value in cast(
                "dict[str, SerializedObject]", serialized_obj["value"]
            ).values():
                add_prefix_to_full_access_path(cast("SerializedObject", value), prefix)
    except (TypeError, KeyError, AttributeError):
        # passed dictionary is not a serialized object
        pass
    return serialized_obj


def serialized_dict_is_nested_object(serialized_dict: SerializedObject) -> bool:
    value = serialized_dict["value"]
    # We are excluding Quantity here as the value corresponding to the "value" key is
    # a dictionary of the form {"magnitude": ..., "unit": ...}
    return serialized_dict["type"] != "Quantity" and (isinstance(value, dict | list))


__all__ = ["Serializer", "dump"]
