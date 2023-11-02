import inspect
import logging
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
        if attr_class_doc != attr_doc:
            return attr_doc
        else:
            return None

    @staticmethod
    def serialize_object(obj: Any):
        obj_type = type(obj).__name__
        value = obj
        readonly = False  # You need to determine how to set this value
        doc = Serializer.get_attribute_doc(obj)
        kwargs: dict[str, Any] = {}

        if isinstance(obj, AbstractDataService):
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

            if type(value).__name__ not in get_component_class_names():
                obj_type = "DataService"

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

        elif isinstance(value, list):
            obj_type = "list"
            value = [Serializer.serialize_object(o) for o in value]

        elif isinstance(value, dict):
            obj_type = "dict"
            value = {key: Serializer.serialize_object(val) for key, val in obj.items()}

        # Special handling for u.Quantity
        elif isinstance(obj, u.Quantity):
            value = {"magnitude": obj.m, "unit": str(obj.u)}

        # Handling for Enums
        elif isinstance(obj, Enum):
            value = obj.name
            if type(obj).__base__.__name__ == "ColouredEnum":
                obj_type = "ColouredEnum"
            else:
                obj_type = "Enum"
            kwargs = {
                "enum": {
                    name: member.value
                    for name, member in obj.__class__.__members__.items()
                },
            }

        # Methods and coroutines
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            sig = inspect.signature(value)

            # Store parameters and their anotations in a dictionary
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
            value = None
            obj_type = "method"
            readonly = True
            kwargs = {
                "async": inspect.iscoroutinefunction(obj),
                "parameters": parameters,
            }

        # Construct the result dictionary
        result = {
            "type": obj_type,
            "value": value,
            "readonly": readonly,
            "doc": doc,
            **kwargs,
        }

        return result


def dump(obj: Any) -> dict[str, Any]:
    return Serializer.serialize_object(obj)
