import inspect
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any, Optional

import pydase.units as u
from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.utils.helpers import get_component_class_names

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


def dump(obj: Any) -> dict[str, Any]:
    return Serializer.serialize_object(obj)
