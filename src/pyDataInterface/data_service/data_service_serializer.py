import asyncio
import inspect
import json
import os
from enum import Enum
from typing import Any

from .task_manager import TaskDict


class DataServiceSerializer:
    def __init__(self, filename: str) -> None:
        self._tasks: dict[str, TaskDict]

    def serialize(  # noqa
        self, tasks: dict[str, Any] = {}
    ) -> dict[str, dict[str, Any]]:
        """
        Serializes the instance into a dictionary, preserving the structure of the
        instance.

        For each attribute, method, and property, the method includes its name, type,
        value, readonly status, and documentation if any in the resulting dictionary.
        Attributes and methods starting with an underscore are ignored.

        For attributes, methods, and properties unique to the class (not inherited from
        the base class), the method uses the format "<prefix>.<key>" for keys in the
        dictionary. If no prefix is provided, the key format is simply "<key>".

        For nested DataService instances, the method serializes recursively and appends
        the key of the nested instance to the prefix in the format "<prefix>.<key>".

        For attributes of type list, each item in the list is serialized individually.
        If an item in the list is an instance of DataService, it is serialized
        recursively with its key in the format "<prefix>.<key>.<item_id>", where
        "item_id" is the id of the item itself.

        Args:
            prefix (str, optional): The prefix for each key in the serialized
            dictionary. This is mainly used when this method is called recursively to
            maintain the structure of nested instances.

        Returns:
            dict: The serialized instance.
        """
        result: dict[str, dict[str, Any]] = {}

        # Get the dictionary of the base class
        base_set = set(type(super()).__dict__)
        # Get the dictionary of the derived class
        derived_set = set(type(self).__dict__)
        # Get the difference between the two dictionaries
        derived_only_set = derived_set - base_set

        instance_dict = set(self.__dict__)
        # Merge the class and instance dictionaries
        merged_set = derived_only_set | instance_dict

        # Iterate over attributes, properties, class attributes, and methods
        for key in merged_set:
            if key.startswith("_"):
                continue  # Skip attributes that start with underscore

            # Skip keys that start with "start_" or "stop_" and end with an async method
            # name
            if (key.startswith("start_") or key.startswith("stop_")) and key.split(
                "_", 1
            )[1] in {
                name
                for name, _ in inspect.getmembers(
                    self, predicate=inspect.iscoroutinefunction
                )
            }:
                continue

            # Get the value of the current attribute or method
            value = getattr(self, key)

            if isinstance(value, DataServiceSerializer):
                result[key] = {
                    "type": type(value).__name__
                    if type(value).__name__ in ("NumberSlider")
                    else "DataService",
                    "value": value.serialize(),
                    "readonly": False,
                    "doc": inspect.getdoc(value),
                }
            elif isinstance(value, list):
                result[key] = {
                    "type": "list",
                    "value": [
                        {
                            "type": "DataService"
                            if isinstance(item, DataServiceSerializer)
                            and type(item).__name__ not in ("NumberSlider")
                            else type(item).__name__,
                            "value": item.serialize()
                            if isinstance(item, DataServiceSerializer)
                            else item,
                            "readonly": False,
                        }
                        for item in value
                    ],
                    "readonly": False,
                }
            elif inspect.isfunction(value) or inspect.ismethod(value):
                sig = inspect.signature(value)
                parameters = {
                    k: v.annotation.__name__
                    if v.annotation is not inspect._empty
                    else None
                    for k, v in sig.parameters.items()
                }
                running_task_info = None
                if key in tasks:  # If there's a running task for this method
                    task_info = tasks[key]
                    running_task_info = task_info["kwargs"]

                result[key] = {
                    "type": "method",
                    "async": asyncio.iscoroutinefunction(value),
                    "parameters": parameters,
                    "doc": inspect.getdoc(value),
                    "value": running_task_info,
                }
            elif isinstance(getattr(self.__class__, key, None), property):
                prop: property = getattr(self.__class__, key)
                result[key] = {
                    "type": type(value).__name__,
                    "value": value,
                    "readonly": prop.fset is None,
                    "doc": inspect.getdoc(prop),
                }
            elif isinstance(value, Enum):
                result[key] = {
                    "type": "Enum",
                    "value": value.name,
                    "enum": {
                        name: member.value
                        for name, member in value.__class__.__members__.items()
                    },
                }
            else:
                result[key] = {
                    "type": type(value).__name__,
                    "value": value,
                    "readonly": False,
                }

        return result
