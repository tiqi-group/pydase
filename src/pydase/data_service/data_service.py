import logging
import warnings
from enum import Enum
from pathlib import Path
from typing import Any, Optional, get_type_hints

import rpyc  # type: ignore

import pydase.units as u
from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.data_service.callback_manager import CallbackManager
from pydase.data_service.task_manager import TaskManager
from pydase.utils.helpers import (
    convert_arguments_to_hinted_types,
    get_class_and_instance_attributes,
    get_object_attr_from_path_list,
    is_property_attribute,
    parse_list_attr_and_index,
    update_value_if_changed,
)
from pydase.utils.serializer import (
    Serializer,
    generate_serialized_data_paths,
    get_nested_dict_by_path,
)
from pydase.utils.warnings import (
    warn_if_instance_class_does_not_inherit_from_DataService,
)

logger = logging.getLogger(__name__)


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
    def __init__(self, **kwargs: Any) -> None:
        self._callback_manager: CallbackManager = CallbackManager(self)
        self._task_manager = TaskManager(self)

        if not hasattr(self, "_autostart_tasks"):
            self._autostart_tasks = {}

        self.__root__: "DataService" = self
        """Keep track of the root object. This helps to filter the emission of
        notifications."""

        filename = kwargs.pop("filename", None)
        if filename is not None:
            warnings.warn(
                "The 'filename' argument is deprecated and will be removed in a future version. "
                "Please pass the 'filename' argument to `pydase.Server`.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._filename: str | Path = filename

        self._callback_manager.register_callbacks()
        self.__check_instance_classes()
        self._initialised = True

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
            # every class defined by the user should inherit from DataService if it is
            # assigned to a public attribute
            if not attr_name.startswith("_"):
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

    def write_to_file(self) -> None:
        """
        Serialize the DataService instance and write it to a JSON file.

        This method is deprecated and will be removed in a future version.
        Service persistence is handled by `pydase.Server` now, instead.
        """

        warnings.warn(
            "'write_to_file' is deprecated and will be removed in a future version. "
            "Service persistence is handled by `pydase.Server` now, instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        if hasattr(self, "_state_manager"):
            getattr(self, "_state_manager").save_state()

    def load_DataService_from_JSON(self, json_dict: dict[str, Any]) -> None:
        warnings.warn(
            "'load_DataService_from_JSON' is deprecated and will be removed in a "
            "future version. "
            "Service persistence is handled by `pydase.Server` now, instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Traverse the serialized representation and set the attributes of the class
        serialized_class = self.serialize()
        for path in generate_serialized_data_paths(json_dict):
            nested_json_dict = get_nested_dict_by_path(json_dict, path)
            value = nested_json_dict["value"]
            value_type = nested_json_dict["type"]

            nested_class_dict = get_nested_dict_by_path(serialized_class, path)
            class_value_type = nested_class_dict.get("type", None)
            if class_value_type == value_type:
                class_attr_is_read_only = nested_class_dict["readonly"]
                if class_attr_is_read_only:
                    logger.debug(
                        f'Attribute "{path}" is read-only. Ignoring value from JSON '
                        "file..."
                    )
                    continue
                # Split the path into parts
                parts = path.split(".")
                attr_name = parts[-1]

                # Convert dictionary into Quantity
                if class_value_type == "Quantity":
                    value = u.convert_to_quantity(value)

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

        For nested DataService instances, the method serializes recursively.
        For attributes of type list, each item in the list is serialized individually.
        If an item in the list is an instance of DataService, it is serialized
        recursively.

        Returns:
            dict: The serialized instance.
        """
        return Serializer.serialize_object(self)["value"]

    def update_DataService_attribute(
        self,
        path_list: list[str],
        attr_name: str,
        value: Any,
    ) -> None:
        warnings.warn(
            "'update_DataService_attribute' is deprecated and will be removed in a "
            "future version. "
            "Service state management is handled by `pydase.data_service.state_manager`"
            "now, instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # If attr_name corresponds to a list entry, extract the attr_name and the index
        attr_name, index = parse_list_attr_and_index(attr_name)
        # Traverse the object according to the path parts
        target_obj = get_object_attr_from_path_list(self, path_list)

        # If the attribute is a property, change it using the setter without getting the
        # property value (would otherwise be bad for expensive getter methods)
        if is_property_attribute(target_obj, attr_name):
            setattr(target_obj, attr_name, value)
            return

        attr = get_object_attr_from_path_list(target_obj, [attr_name])
        if attr is None:
            return

        self.__set_attribute_based_on_type(
            target_obj, attr_name, attr, value, index, path_list
        )
