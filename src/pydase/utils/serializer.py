import inspect
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any, Optional, cast

import pydase.units as u
from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.utils.helpers import (
    STANDARD_TYPES,
    get_component_class_names,
    parse_list_attr_and_index,
)

logger = logging.getLogger(__name__)


class Serializer:
    @staticmethod
    def get_attribute_doc(attr: Any) -> Optional[str]:
        """This function takes an input attribute attr and returns its documentation
        string if it's different from the documentation of its type, otherwise,
        it returns None.
        """
        attr_doc = inspect.getdoc(attr)
        attr_class_doc = inspect.getdoc(type(attr))
        return attr_doc if attr_class_doc != attr_doc else None

    @staticmethod
    def serialize_object(obj: Any) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if isinstance(obj, AbstractDataService):
            result = Serializer._serialize_DataService(obj)

        elif isinstance(obj, list):
            result = Serializer._serialize_list(obj)

        elif isinstance(obj, dict):
            result = Serializer._serialize_dict(obj)

        # Special handling for u.Quantity
        elif isinstance(obj, u.Quantity):
            result = Serializer._serialize_Quantity(obj)

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
            doc = Serializer.get_attribute_doc(obj)
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
        doc = Serializer.get_attribute_doc(obj)
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
    def _serialize_Quantity(obj: u.Quantity) -> dict[str, Any]:
        obj_type = "Quantity"
        readonly = False
        doc = Serializer.get_attribute_doc(obj)
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
        doc = Serializer.get_attribute_doc(obj)
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
        doc = Serializer.get_attribute_doc(obj)
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
        doc = Serializer.get_attribute_doc(obj)

        # Store parameters and their anotations in a dictionary
        sig = inspect.signature(obj)
        parameters: dict[str, Optional[str]] = {}

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
    def _serialize_DataService(obj: AbstractDataService) -> dict[str, Any]:
        readonly = False
        doc = Serializer.get_attribute_doc(obj)
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
            if (key.startswith("start_") or key.startswith("stop_")) and key.split(
                "_", 1
            )[1] in {
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
                value[key]["doc"] = Serializer.get_attribute_doc(
                    prop
                )  # overwrite the doc

        return {
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    @staticmethod
    def update_serialization_dict(
        serialization_dict: dict[str, Any], path: str, value: Any
    ) -> None:
        """
        Set the value associated with a specific key in a dictionary given a path.

        This function traverses the dictionary according to the path provided and
        sets the value at that path. The path is a string with dots connecting
        the levels and brackets indicating list indices.

        Args:
            data_dict (dict): The cache dictionary to set the value in.
            path (str): The path to where the value should be set in the dictionary.
            value (Any): The value to be set at the specified path in the dictionary.

        Examples:
            Let's consider the following dictionary:

            cache = {
                "attr1": {"type": "int", "value": 10},
                "attr2": {
                    "type": "MyClass",
                    "value": {"attr3": {"type": "float", "value": 20.5}}
                }
            }

            The function can be used to set the value of 'attr1' as follows:
            set_nested_value_in_cache(cache, "attr1", 15)

            It can also be used to set the value of 'attr3', which is nested within
            'attr2', as follows:
            set_nested_value_in_cache(cache, "attr2.attr3", 25.0)
        """

        parts, attr_name = path.split(".")[:-1], path.split(".")[-1]
        current_dict: dict[str, Any] = serialization_dict
        index: Optional[int] = None

        for path_part in parts:
            # Check if the key contains an index part like 'attr_name[<index>]'
            path_part, index = parse_list_attr_and_index(path_part)

            current_dict = cast(dict[str, Any], current_dict.get(path_part, None))

            if not isinstance(current_dict, dict):
                # key does not exist in dictionary, e.g. when class does not have this
                # attribute
                return

            if index is not None:
                try:
                    current_dict = cast(dict[str, Any], current_dict["value"][index])
                except Exception as e:
                    # TODO: appending to a list will probably be done here
                    logger.error(f"Could not change {path}... {e}")
                    return

            # When the attribute is a class instance, the attributes are nested in the
            # "value" key
            if (
                current_dict["type"] not in STANDARD_TYPES
                and current_dict["type"] != "method"
            ):
                current_dict = cast(dict[str, Any], current_dict.get("value", None))  # type: ignore

            index = None

        # setting the new value
        serialized_value = dump(value)
        current_dict[attr_name]["value"] = serialized_value["value"]
        current_dict[attr_name]["type"] = serialized_value["type"]


def dump(obj: Any) -> dict[str, Any]:
    return Serializer.serialize_object(obj)
