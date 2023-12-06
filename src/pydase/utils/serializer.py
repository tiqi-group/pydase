import inspect
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any

import pydase.units as u
from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.utils.helpers import (
    get_attribute_doc,
    get_component_class_names,
    parse_list_attr_and_index,
)

logger = logging.getLogger(__name__)


class SerializationPathError(Exception):
    pass


class SerializationValueError(Exception):
    pass


class Serializer:
    @staticmethod
    def serialize_object(obj: Any) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if isinstance(obj, AbstractDataService):
            result = Serializer._serialize_data_service(obj)

        elif isinstance(obj, list):
            result = Serializer._serialize_list(obj)

        elif isinstance(obj, dict):
            result = Serializer._serialize_dict(obj)

        # Special handling for u.Quantity
        elif isinstance(obj, u.Quantity):
            result = Serializer._serialize_quantity(obj)

        # Handling for Enums
        elif isinstance(obj, Enum):
            result = Serializer._serialize_enum(obj)

        # Methods and coroutines
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            result = Serializer._serialize_method(obj)

        else:
            obj_type = type(obj).__name__
            value = obj
            readonly = False
            doc = get_attribute_doc(obj)
            result = {
                "type": obj_type,
                "value": value,
                "readonly": readonly,
                "doc": doc,
            }

        return result

    @staticmethod
    def _serialize_enum(obj: Enum) -> dict[str, Any]:
        value = obj.name
        readonly = False
        doc = get_attribute_doc(obj)
        if type(obj).__base__.__name__ == "ColouredEnum":
            obj_type = "ColouredEnum"
        else:
            obj_type = "Enum"

        return {
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
            "enum": {
                name: member.value for name, member in obj.__class__.__members__.items()
            },
        }

    @staticmethod
    def _serialize_quantity(obj: u.Quantity) -> dict[str, Any]:
        obj_type = "Quantity"
        readonly = False
        doc = get_attribute_doc(obj)
        value = {"magnitude": obj.m, "unit": str(obj.u)}
        return {
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @staticmethod
    def _serialize_dict(obj: dict[str, Any]) -> dict[str, Any]:
        obj_type = "dict"
        readonly = False
        doc = get_attribute_doc(obj)
        value = {key: Serializer.serialize_object(val) for key, val in obj.items()}
        return {
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @staticmethod
    def _serialize_list(obj: list[Any]) -> dict[str, Any]:
        obj_type = "list"
        readonly = False
        doc = get_attribute_doc(obj)
        value = [Serializer.serialize_object(o) for o in obj]
        return {
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @staticmethod
    def _serialize_method(obj: Callable[..., Any]) -> dict[str, Any]:
        obj_type = "method"
        value = None
        readonly = True
        doc = get_attribute_doc(obj)

        # Store parameters and their anotations in a dictionary
        sig = inspect.signature(obj)
        parameters: dict[str, str | None] = {}

        for k, v in sig.parameters.items():
            annotation = v.annotation
            if annotation is not inspect._empty:
                if isinstance(annotation, type):
                    # Handle regular types
                    parameters[k] = annotation.__name__
                else:
                    # Union, string annotation, Literal types, ...
                    parameters[k] = str(annotation)
            else:
                parameters[k] = None

        return {
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
            "async": inspect.iscoroutinefunction(obj),
            "parameters": parameters,
        }

    @staticmethod
    def _serialize_data_service(obj: AbstractDataService) -> dict[str, Any]:
        readonly = False
        doc = get_attribute_doc(obj)
        obj_type = type(obj).__name__
        if type(obj).__name__ not in get_component_class_names():
            obj_type = "DataService"

        # Get the dictionary of the base class
        base_set = set(type(obj).__base__.__dict__)
        # Get the dictionary of the derived class
        derived_set = set(type(obj).__dict__)
        # Get the difference between the two dictionaries
        derived_only_set = derived_set - base_set

        instance_dict = set(obj.__dict__)
        # Merge the class and instance dictionaries
        merged_set = derived_only_set | instance_dict
        value = {}

        # Iterate over attributes, properties, class attributes, and methods
        for key in sorted(merged_set):
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

            value[key] = Serializer.serialize_object(val)

            # If there's a running task for this method
            if key in obj._task_manager.tasks:
                task_info = obj._task_manager.tasks[key]
                value[key]["value"] = task_info["kwargs"]

            # If the DataService attribute is a property
            if isinstance(getattr(obj.__class__, key, None), property):
                prop: property = getattr(obj.__class__, key)
                value[key]["readonly"] = prop.fset is None
                value[key]["doc"] = get_attribute_doc(prop)  # overwrite the doc

        return {
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }


def dump(obj: Any) -> dict[str, Any]:
    return Serializer.serialize_object(obj)


def set_nested_value_by_path(
    serialization_dict: dict[str, Any], path: str, value: Any
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
    current_dict: dict[str, Any] = serialization_dict

    try:
        for path_part in parent_path_parts:
            current_dict = get_next_level_dict_by_key(
                current_dict, path_part, allow_append=False
            )
            current_dict = current_dict["value"]

        current_dict = get_next_level_dict_by_key(
            current_dict, attr_name, allow_append=True
        )
    except (SerializationPathError, SerializationValueError, KeyError) as e:
        logger.error(e)
        return

    # setting the new value
    serialized_value = dump(value)
    if "readonly" in current_dict:
        if current_dict["type"] != "method":
            current_dict["type"] = serialized_value["type"]
        current_dict["value"] = serialized_value["value"]
    else:
        current_dict.update(serialized_value)


def get_nested_dict_by_path(
    serialization_dict: dict[str, Any],
    path: str,
) -> dict[str, Any]:
    parent_path_parts, attr_name = path.split(".")[:-1], path.split(".")[-1]
    current_dict: dict[str, Any] = serialization_dict

    for path_part in parent_path_parts:
        current_dict = get_next_level_dict_by_key(
            current_dict, path_part, allow_append=False
        )
        current_dict = current_dict["value"]
    return get_next_level_dict_by_key(current_dict, attr_name, allow_append=False)


def get_next_level_dict_by_key(
    serialization_dict: dict[str, Any],
    attr_name: str,
    *,
    allow_append: bool = False,
) -> dict[str, Any]:
    """
    Retrieve a nested dictionary entry or list item from a data structure serialized
    with `pydase.utils.serializer.Serializer`.

    Args:
        serialization_dict: The base dictionary representing serialized data.
        attr_name: The key name representing the attribute in the dictionary,
            e.g. 'list_attr[0]' or 'attr'
        allow_append: Flag to allow appending a new entry if `index` is out of range by
            one.

    Returns:
        The dictionary or list item corresponding to the attribute and index.

    Raises:
        SerializationPathError: If the path composed of `attr_name` and `index` is
                                invalid or leads to an IndexError or KeyError.
        SerializationValueError: If the expected nested structure is not a dictionary.
    """
    # Check if the key contains an index part like 'attr_name[<index>]'
    attr_name, index = parse_list_attr_and_index(attr_name)

    try:
        if index is not None:
            serialization_dict = serialization_dict[attr_name]["value"][index]
        else:
            serialization_dict = serialization_dict[attr_name]
    except IndexError as e:
        if allow_append and index == len(serialization_dict[attr_name]["value"]):
            # Appending to list
            serialization_dict[attr_name]["value"].append({})
            serialization_dict = serialization_dict[attr_name]["value"][index]
        else:
            raise SerializationPathError(
                f"Error occured trying to change '{attr_name}[{index}]': {e}"
            )
    except KeyError:
        raise SerializationPathError(
            f"Error occured trying to access the key '{attr_name}': it is either "
            "not present in the current dictionary or its value does not contain "
            "a 'value' key."
        )

    if not isinstance(serialization_dict, dict):
        raise SerializationValueError(
            f"Expected a dictionary at '{attr_name}', but found type "
            f"'{type(serialization_dict).__name__}' instead."
        )

    return serialization_dict


def generate_serialized_data_paths(
    data: dict[str, Any], parent_path: str = ""
) -> list[str]:
    """
    Generate a list of access paths for all attributes in a dictionary representing
    data serialized with `pydase.utils.serializer.Serializer`, excluding those that are
    methods.

    Args:
        data: The dictionary representing serialized data, typically produced by
            `pydase.utils.serializer.Serializer`.
        parent_path: The base path to prepend to the keys in the `data` dictionary to
            form the access paths. Defaults to an empty string.

    Returns:
        A list of strings where each string is a dot-notation access path to an
        attribute in the serialized data.
    """

    paths: list[str] = []
    for key, value in data.items():
        if value["type"] == "method":
            # ignoring methods
            continue
        new_path = f"{parent_path}.{key}" if parent_path else key
        if isinstance(value["value"], dict) and value["type"] != "Quantity":
            paths.extend(generate_serialized_data_paths(value["value"], new_path))
        elif isinstance(value["value"], list):
            for index, item in enumerate(value["value"]):
                indexed_key_path = f"{new_path}[{index}]"
                if isinstance(item["value"], dict):
                    paths.extend(
                        generate_serialized_data_paths(item["value"], indexed_key_path)
                    )
                else:
                    paths.append(indexed_key_path)
        else:
            paths.append(new_path)
    return paths
