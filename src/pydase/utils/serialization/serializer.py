from __future__ import annotations

import inspect
import logging
import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, cast

import pydase.units as u
from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.data_service.task_manager import TaskStatus
from pydase.utils.helpers import (
    get_attribute_doc,
    get_component_classes,
    get_data_service_class_reference,
    parse_keyed_attribute,
    render_in_frontend,
)
from pydase.utils.serialization.types import (
    DataServiceTypes,
    SerializedBool,
    SerializedDataService,
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

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class SerializationError(Exception):
    pass


class SerializationPathError(Exception):
    pass


class SerializationValueError(Exception):
    pass


class Serializer:
    @staticmethod
    def serialize_object(obj: Any, access_path: str = "") -> SerializedObject:  # noqa: C901
        result: SerializedObject

        if isinstance(obj, Exception):
            result = Serializer._serialize_exception(obj)

        elif isinstance(obj, AbstractDataService):
            result = Serializer._serialize_data_service(obj, access_path=access_path)

        elif isinstance(obj, list):
            result = Serializer._serialize_list(obj, access_path=access_path)

        elif isinstance(obj, dict):
            result = Serializer._serialize_dict(obj, access_path=access_path)

        # Special handling for u.Quantity
        elif isinstance(obj, u.Quantity):
            result = Serializer._serialize_quantity(obj, access_path=access_path)

        # Handling for Enums
        elif isinstance(obj, Enum):
            result = Serializer._serialize_enum(obj, access_path=access_path)

        # Methods and coroutines
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            result = Serializer._serialize_method(obj, access_path=access_path)

        elif isinstance(obj, int | float | bool | str | None):
            result = Serializer._serialize_primitive(obj, access_path=access_path)

        try:
            return result
        except UnboundLocalError:
            raise SerializationError(
                f"Could not serialized object of type {type(obj)}."
            )

    @staticmethod
    def _serialize_primitive(
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

    @staticmethod
    def _serialize_exception(obj: Exception) -> SerializedException:
        return {
            "full_access_path": "",
            "doc": None,
            "readonly": True,
            "type": "Exception",
            "value": obj.args[0],
            "name": obj.__class__.__name__,
        }

    @staticmethod
    def _serialize_enum(obj: Enum, access_path: str = "") -> SerializedEnum:
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

    @staticmethod
    def _serialize_quantity(
        obj: u.Quantity, access_path: str = ""
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

    @staticmethod
    def _serialize_dict(obj: dict[str, Any], access_path: str = "") -> SerializedDict:
        readonly = False
        doc = get_attribute_doc(obj)
        value = {
            key: Serializer.serialize_object(val, access_path=f'{access_path}["{key}"]')
            for key, val in obj.items()
        }
        return {
            "full_access_path": access_path,
            "type": "dict",
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @staticmethod
    def _serialize_list(obj: list[Any], access_path: str = "") -> SerializedList:
        readonly = False
        doc = get_attribute_doc(obj)
        value = [
            Serializer.serialize_object(o, access_path=f"{access_path}[{i}]")
            for i, o in enumerate(obj)
        ]
        return {
            "full_access_path": access_path,
            "type": "list",
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @staticmethod
    def _serialize_method(
        obj: Callable[..., Any], access_path: str = ""
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
                dict[str, Any], {} if v.default == inspect._empty else dump(v.default)
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

    @staticmethod
    def _serialize_data_service(
        obj: AbstractDataService, access_path: str = ""
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

            # Skip keys that start with "start_" or "stop_" and end with an async
            # method name
            if key.startswith(("start_", "stop_")) and key.split("_", 1)[1] in {
                name
                for name, _ in inspect.getmembers(
                    obj, predicate=inspect.iscoroutinefunction
                )
            }:
                continue

            val = getattr(obj, key)

            path = f"{access_path}.{key}" if access_path else key
            serialized_object = Serializer.serialize_object(val, access_path=path)

            # If there's a running task for this method
            if serialized_object["type"] == "method" and key in obj._task_manager.tasks:
                serialized_object["value"] = TaskStatus.RUNNING.name

            value[key] = serialized_object

            # If the DataService attribute is a property
            if isinstance(getattr(obj.__class__, key, None), property):
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


def dump(obj: Any) -> SerializedObject:
    return Serializer.serialize_object(obj)


def set_nested_value_by_path(
    serialization_dict: dict[str, SerializedObject], path: str, value: Any
) -> None:
    """
    Set a value in a nested dictionary structure, which conforms to the serialization
    format used by `pydase.utils.serializer.Serializer`, using a dot-notation path.

    Args:
        serialization_dict:
            The base dictionary representing data serialized with
            `pydase.utils.serializer.Serializer`.
        path:
            The dot-notation path (e.g., 'attr1.attr2[0].attr3') indicating where to
            set the value.
        value:
            The new value to set at the specified path.

    Note:
        - If the index equals the length of the list, the function will append the
          serialized representation of the 'value' to the list.
    """

    parent_path_parts, attr_name = path.split(".")[:-1], path.split(".")[-1]
    current_dict: dict[str, SerializedObject] = serialization_dict

    try:
        for path_part in parent_path_parts:
            next_level_serialized_object = get_next_level_dict_by_key(
                current_dict, path_part, allow_append=False
            )
            current_dict = cast(
                dict[str, SerializedObject], next_level_serialized_object["value"]
            )

        next_level_serialized_object = get_next_level_dict_by_key(
            current_dict, attr_name, allow_append=True
        )
    except (SerializationPathError, SerializationValueError, KeyError) as e:
        logger.error(e)
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
    serialization_dict: dict[str, SerializedObject],
    path: str,
) -> SerializedObject:
    parent_path_parts, attr_name = path.split(".")[:-1], path.split(".")[-1]
    current_dict: dict[str, SerializedObject] = serialization_dict

    for path_part in parent_path_parts:
        next_level_serialized_object = get_next_level_dict_by_key(
            current_dict, path_part, allow_append=False
        )
        current_dict = cast(
            dict[str, SerializedObject], next_level_serialized_object["value"]
        )
    return get_next_level_dict_by_key(current_dict, attr_name, allow_append=False)


def create_empty_serialized_object() -> SerializedObject:
    """Create a new empty serialized object."""

    return {
        "full_access_path": "",
        "value": None,
        "type": "None",
        "doc": None,
        "readonly": False,
    }


def ensure_exists(
    container: dict[str, SerializedObject], key: str, *, allow_add_key: bool
) -> SerializedObject:
    """Ensure the key exists in the dictionary, append if necessary and allowed."""

    try:
        return container[key]
    except KeyError:
        if not allow_add_key:
            raise SerializationPathError(f"Key '{key}' does not exist.")
        container[key] = create_empty_serialized_object()
        return container[key]


def get_nested_value(
    obj: SerializedObject, key: Any, allow_append: bool
) -> SerializedObject:
    """Retrieve or append the nested value based on the key."""

    value = cast(list[SerializedObject] | dict[Any, SerializedObject], obj["value"])
    try:
        return value[key]
    except KeyError:
        if allow_append:
            value[key] = create_empty_serialized_object()
            return value[key]
        raise
    except IndexError:
        if allow_append and key == len(value):
            cast(list[SerializedObject], value).append(create_empty_serialized_object())
            return value[key]
        raise


def get_next_level_dict_by_key(
    serialization_dict: dict[str, SerializedObject],
    attr_name: str,
    *,
    allow_append: bool = False,
) -> SerializedObject:
    """
    Retrieve a nested dictionary entry or list item from a serialized data structure.

    This function supports deep retrieval from a nested serialization structure
    based on an attribute name that may specify direct keys or indexed list elements.
    If specified keys or indexes do not exist, the function can append new elements
    to lists if `allow_append` is True and the missing element is exactly the next
    sequential index.

    Args:
        serialization_dict: dict[str, SerializedObject]
            The base dictionary representing serialized data.
        attr_name: str
            The key name representing the attribute in the dictionary, which may include
            direct keys or indexes (e.g., 'list_attr[0]', 'dict_attr["key"]' or 'attr').
        allow_append: bool
            Flag to allow appending a new entry if the specified index is out of range
            by exactly one position.

    Returns:
        SerializedObject
            The dictionary or list item corresponding to the specified attribute and
            index.

    Raises:
        SerializationPathError:
            If the path composed of `attr_name` and any specified index is invalid, or
            leads to an IndexError or KeyError. This error is also raised if an attempt
            to access a nonexistent key or index occurs without permission to append.
        SerializationValueError:
            If the retrieval results in an object that is expected to be a dictionary
            but is not, indicating a mismatch between expected and actual serialized
            data structure.
    """

    # Implementation remains the same as the earlier code snippet
    # Check if the key contains an index part like 'attr_name[<key>]'
    attr_name_base, key = parse_keyed_attribute(attr_name)

    # Add the attr_name key to the serialized object if it does not exist AND the key
    # is None. Otherwise, we are trying to add a key-value pair/item to a non-existing
    # object
    serialized_object = ensure_exists(
        serialization_dict, attr_name_base, allow_add_key=allow_append and key is None
    )

    if key is not None:
        try:
            serialized_object = get_nested_value(
                serialized_object, key, allow_append=allow_append
            )
        except (KeyError, IndexError) as e:
            raise SerializationPathError(
                f"Error occured trying to change '{attr_name}': {e}"
            )

    if not isinstance(serialized_object, dict):
        raise SerializationValueError(
            f"Expected a dictionary at '{attr_name_base}', but found type "
            f"'{type(serialized_object).__name__}' instead."
        )

    return serialized_object


def generate_serialized_data_paths(
    data: dict[str, Any], parent_path: str = ""
) -> list[str]:
    """
    Generate a list of access paths for all attributes in a dictionary representing
    data serialized with `pydase.utils.serializer.Serializer`, excluding those that are
    methods. This function handles nested structures, including lists, by generating
    paths for each element in the nested lists.

    Args:
        data (dict[str, Any]): The dictionary representing serialized data, typically
            produced by `pydase.utils.serializer.Serializer`.
        parent_path (str, optional): The base path to prepend to the keys in the `data`
            dictionary to form the access paths. Defaults to an empty string.

    Returns:
        list[str]: A list of strings where each string is a dot-notation access path
        to an attribute in the serialized data. For list elements, the path includes
        the index in square brackets.
    """

    paths: list[str] = []
    for key, value in data.items():
        new_path = f"{parent_path}.{key}" if parent_path else key
        paths.append(new_path)
        if serialized_dict_is_nested_object(value):
            if isinstance(value["value"], list):
                for index, item in enumerate(value["value"]):
                    indexed_key_path = f"{new_path}[{index}]"
                    paths.append(indexed_key_path)
                    if serialized_dict_is_nested_object(item):
                        paths.extend(
                            generate_serialized_data_paths(
                                item["value"], indexed_key_path
                            )
                        )
                continue
            paths.extend(generate_serialized_data_paths(value["value"], new_path))
    return paths


def serialized_dict_is_nested_object(serialized_dict: SerializedObject) -> bool:
    return (
        serialized_dict["type"] != "Quantity"
        and isinstance(serialized_dict["value"], dict)
    ) or isinstance(serialized_dict["value"], list)
