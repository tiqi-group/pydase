import asyncio
import inspect
import json
import os
from enum import Enum
from typing import Any, Optional, cast, get_type_hints

import rpyc
from loguru import logger

import pydase.units as u
from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.data_service.callback_manager import CallbackManager
from pydase.data_service.task_manager import TaskManager
from pydase.utils.helpers import (
    convert_arguments_to_hinted_types,
    generate_paths_from_DataService_dict,
    get_class_and_instance_attributes,
    get_component_class_names,
    get_nested_value_from_DataService_by_path_and_key,
    get_object_attr_from_path,
    is_property_attribute,
    parse_list_attr_and_index,
    update_value_if_changed,
)
from pydase.utils.warnings import (
    warn_if_instance_class_does_not_inherit_from_DataService,
)


def process_callable_attribute(attr: Any, args: dict[str, Any]) -> Any:
    converted_args_or_error_msg = convert_arguments_to_hinted_types(
        args, get_type_hints(attr)
    )
    return (
        attr(**converted_args_or_error_msg)
        if not isinstance(converted_args_or_error_msg, str)
        else converted_args_or_error_msg
    )


class DataService(rpyc.Service, AbstractDataService):
    def __init__(self, filename: Optional[str] = None) -> None:
        self._callback_manager: CallbackManager = CallbackManager(self)
        self._task_manager = TaskManager(self)

        if not hasattr(self, "_autostart_tasks"):
            self._autostart_tasks = {}

        self.__root__: "DataService" = self
        """Keep track of the root object. This helps to filter the emission of
        notifications. This overwrite the TaksManager's __root__ attribute."""

        self._filename: Optional[str] = filename

        self._callback_manager.register_callbacks()
        self.__check_instance_classes()
        self._initialised = True
        self._load_values_from_json()

    def __setattr__(self, __name: str, __value: Any) -> None:
        # converting attributes that are not properties
        if not isinstance(getattr(type(self), __name, None), property):
            current_value = getattr(self, __name, None)
            # parse ints into floats if current value is a float
            if isinstance(current_value, float) and isinstance(__value, int):
                __value = float(__value)

            if isinstance(current_value, u.Quantity):
                __value = u.convert_to_quantity(__value, str(current_value.u))

        super().__setattr__(__name, __value)

        if self.__dict__.get("_initialised") and not __name == "_initialised":
            for callback in self._callback_manager.callbacks:
                callback(__name, __value)
        elif __name.startswith(f"_{self.__class__.__name__}__"):
            logger.warning(
                f"Warning: You should not set private but rather protected attributes! "
                f"Use {__name.replace(f'_{self.__class__.__name__}__', '_')} instead "
                f"of {__name.replace(f'_{self.__class__.__name__}__', '__')}."
            )

    def __check_instance_classes(self) -> None:
        for attr_name, attr_value in get_class_and_instance_attributes(self).items():
            # every class defined by the user should inherit from DataService
            if not attr_name.startswith("_DataService__"):
                warn_if_instance_class_does_not_inherit_from_DataService(attr_value)

    def __set_attribute_based_on_type(  # noqa:CFQ002
        self,
        target_obj: Any,
        attr_name: str,
        attr: Any,
        value: Any,
        index: Optional[int],
        path_list: list[str],
    ) -> None:
        if isinstance(attr, Enum):
            update_value_if_changed(target_obj, attr_name, attr.__class__[value])
        elif isinstance(attr, list) and index is not None:
            update_value_if_changed(attr, index, value)
        elif isinstance(attr, DataService) and isinstance(value, dict):
            for key, v in value.items():
                self.update_DataService_attribute([*path_list, attr_name], key, v)
        elif callable(attr):
            process_callable_attribute(attr, value["args"])
        else:
            update_value_if_changed(target_obj, attr_name, value)

    def _rpyc_getattr(self, name: str) -> Any:
        if name.startswith("_"):
            # disallow special and private attributes
            raise AttributeError("cannot access private/special names")
        # allow all other attributes
        return getattr(self, name)

    def _rpyc_setattr(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            # disallow special and private attributes
            raise AttributeError("cannot access private/special names")

        # check if the attribute has a setter method
        attr = getattr(self, name, None)
        if isinstance(attr, property) and attr.fset is None:
            raise AttributeError(f"{name} attribute does not have a setter method")

        # allow all other attributes
        setattr(self, name, value)

    def _load_values_from_json(self) -> None:
        if self._filename is not None:
            # Check if the file specified by the filename exists
            if os.path.exists(self._filename):
                with open(self._filename, "r") as f:
                    # Load JSON data from file and update class attributes with these
                    # values
                    self.load_DataService_from_JSON(cast(dict[str, Any], json.load(f)))

    def write_to_file(self) -> None:
        """
        Serialize the DataService instance and write it to a JSON file.

        Args:
            filename (str): The name of the file to write to.
        """
        if self._filename is not None:
            with open(self._filename, "w") as f:
                json.dump(self.serialize(), f, indent=4)
        else:
            logger.error(
                f"Class {self.__class__.__name__} was not initialised with a filename. "
                'Skipping "write_to_file"...'
            )

    def load_DataService_from_JSON(self, json_dict: dict[str, Any]) -> None:
        # Traverse the serialized representation and set the attributes of the class
        serialized_class = self.serialize()
        for path in generate_paths_from_DataService_dict(json_dict):
            value = get_nested_value_from_DataService_by_path_and_key(
                json_dict, path=path
            )
            value_type = get_nested_value_from_DataService_by_path_and_key(
                json_dict, path=path, key="type"
            )
            class_value_type = get_nested_value_from_DataService_by_path_and_key(
                serialized_class, path=path, key="type"
            )
            if class_value_type == value_type:
                class_attr_is_read_only = (
                    get_nested_value_from_DataService_by_path_and_key(
                        serialized_class, path=path, key="readonly"
                    )
                )
                if class_attr_is_read_only:
                    logger.debug(
                        f'Attribute "{path}" is read-only. Ignoring value from JSON '
                        "file..."
                    )
                    continue
                # Split the path into parts
                parts = path.split(".")
                attr_name = parts[-1]

                self.update_DataService_attribute(parts[:-1], attr_name, value)
            else:
                logger.info(
                    f'Attribute type of "{path}" changed from "{value_type}" to '
                    f'"{class_value_type}". Ignoring value from JSON file...'
                )

    def serialize(self) -> dict[str, dict[str, Any]]:  # noqa
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

        # Iterate over attributes, properties, class attributes, and methods
        for key in sorted(merged_set):
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

            if isinstance(value, DataService):
                result[key] = {
                    "type": type(value).__name__
                    if type(value).__name__ in get_component_class_names()
                    else "DataService",
                    "value": value.serialize(),
                    "readonly": False,
                    "doc": get_attribute_doc(value),
                }
            elif isinstance(value, list):
                result[key] = {
                    "type": "list",
                    "value": [
                        {
                            "type": type(item).__name__
                            if not isinstance(item, DataService)
                            or type(item).__name__ in get_component_class_names()
                            else "DataService",
                            "value": item.serialize()
                            if isinstance(item, DataService)
                            else item,
                            "readonly": False,
                            "doc": get_attribute_doc(value),
                        }
                        for item in value
                    ],
                    "readonly": False,
                }
            elif inspect.isfunction(value) or inspect.ismethod(value):
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
                            parameters[k] = str(annotation)
                    else:
                        parameters[k] = None
                running_task_info = None
                if (
                    key in self._task_manager.tasks
                ):  # If there's a running task for this method
                    task_info = self._task_manager.tasks[key]
                    running_task_info = task_info["kwargs"]

                result[key] = {
                    "type": "method",
                    "async": asyncio.iscoroutinefunction(value),
                    "parameters": parameters,
                    "doc": get_attribute_doc(value),
                    "readonly": True,
                    "value": running_task_info,
                }
            elif isinstance(getattr(self.__class__, key, None), property):
                prop: property = getattr(self.__class__, key)
                result[key] = {
                    "type": type(value).__name__,
                    "value": value
                    if not isinstance(value, u.Quantity)
                    else {"magnitude": value.m, "unit": str(value.u)},
                    "readonly": prop.fset is None,
                    "doc": get_attribute_doc(prop),
                }
            elif isinstance(value, Enum):
                result[key] = {
                    "type": "Enum",
                    "value": value.name,
                    "enum": {
                        name: member.value
                        for name, member in value.__class__.__members__.items()
                    },
                    "readonly": False,
                    "doc": get_attribute_doc(value),
                }
            else:
                result[key] = {
                    "type": type(value).__name__,
                    "value": value
                    if not isinstance(value, u.Quantity)
                    else {"magnitude": value.m, "unit": str(value.u)},
                    "readonly": False,
                    "doc": get_attribute_doc(value),
                }

        return result

    def update_DataService_attribute(
        self,
        path_list: list[str],
        attr_name: str,
        value: Any,
    ) -> None:
        # If attr_name corresponds to a list entry, extract the attr_name and the index
        attr_name, index = parse_list_attr_and_index(attr_name)
        # Traverse the object according to the path parts
        target_obj = get_object_attr_from_path(self, path_list)

        # If the attribute is a property, change it using the setter without getting the
        # property value (would otherwise be bad for expensive getter methods)
        if is_property_attribute(target_obj, attr_name):
            setattr(target_obj, attr_name, value)
            return

        attr = get_object_attr_from_path(target_obj, [attr_name])
        if attr is None:
            return

        self.__set_attribute_based_on_type(
            target_obj, attr_name, attr, value, index, path_list
        )
