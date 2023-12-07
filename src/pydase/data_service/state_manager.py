import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pydase.units as u
from pydase.data_service.data_service_cache import DataServiceCache
from pydase.utils.helpers import (
    get_object_attr_from_path_list,
    parse_list_attr_and_index,
)
from pydase.utils.serializer import (
    dump,
    generate_serialized_data_paths,
    get_nested_dict_by_path,
)

if TYPE_CHECKING:
    from pydase import DataService

logger = logging.getLogger(__name__)


def load_state(func: Callable[..., Any]) -> Callable[..., Any]:
    """This function should be used as a decorator on property setters to indicate that
    the value should be loaded from the JSON file.

    Example:
    >>>     class Service(pydase.DataService):
    ...         _name = "Service"
    ...
    ...         @property
    ...         def name(self) -> str:
    ...             return self._name
    ...
    ...         @name.setter
    ...         @load_state
    ...         def name(self, value: str) -> None:
    ...             self._name = value
    """

    func._load_state = True  # type: ignore[attr-defined]
    return func


def has_load_state_decorator(prop: property) -> bool:
    """Determines if the property's setter method is decorated with the `@load_state`
    decorator.
    """

    try:
        return prop.fset._load_state  # type: ignore[union-attr]
    except AttributeError:
        return False


class StateManager:
    """
    Manages the state of a DataService instance, serving as both a cache and a
    persistence layer. It is designed to provide quick access to the latest known state
    for newly connecting web clients without the need for expensive property accesses
    that may involve complex calculations or I/O operations.

    The StateManager listens for state change notifications from the DataService's
    callback manager and updates its cache accordingly. This cache does not always
    reflect the most current complex property states but rather retains the value from
    the last known state, optimizing for performance and reducing the load on the
    system.

    While the StateManager ensures that the cached state is as up-to-date as possible,
    it does not autonomously update complex properties of the DataService. Such
    properties must be updated programmatically, for instance, by invoking specific
    tasks or methods that trigger the necessary operations to refresh their state.

    The cached state maintained by the StateManager is particularly useful for web
    clients that connect to the system and need immediate access to the current state of
    the DataService. By avoiding direct and potentially costly property accesses, the
    StateManager provides a snapshot of the DataService's state that is sufficiently
    accurate for initial rendering and interaction.

    Attributes:
        cache (dict[str, Any]):
            A dictionary cache of the DataService's state.
        filename (str):
            The file name used for storing the DataService's state.
        service (DataService):
            The DataService instance whose state is being managed.

    Note:
        The StateManager's cache updates are triggered by notifications and do not
        include autonomous updates of complex DataService properties, which must be
        managed programmatically. The cache serves the purpose of providing immediate
        state information to web clients, reflecting the state after the last property
        update.
    """

    def __init__(
        self, service: "DataService", filename: str | Path | None = None
    ) -> None:
        self.filename = getattr(service, "_filename", None)

        if filename is not None:
            if self.filename is not None:
                logger.warning(
                    "Overwriting filename '%s' with '%s'.", self.filename, filename
                )
            self.filename = filename

        self.service = service
        self._data_service_cache = DataServiceCache(self.service)

    @property
    def cache(self) -> dict[str, Any]:
        """Returns the cached DataService state."""
        return self._data_service_cache.cache

    def save_state(self) -> None:
        """
        Saves the DataService's current state to a JSON file defined by `self.filename`.
        Logs an error if `self.filename` is not set.
        """

        if self.filename is not None:
            with open(self.filename, "w") as f:
                json.dump(self.cache, f, indent=4)
        else:
            logger.info(
                "State manager was not initialised with a filename. Skipping "
                "'save_state'..."
            )

    def load_state(self) -> None:
        """
        Loads the DataService's state from a JSON file defined by `self.filename`.
        Updates the service's attributes, respecting type and read-only constraints.
        """

        # Traverse the serialized representation and set the attributes of the class
        json_dict = self._get_state_dict_from_json_file()
        if json_dict == {}:
            logger.debug("Could not load the service state.")
            return

        for path in generate_serialized_data_paths(json_dict):
            nested_json_dict = get_nested_dict_by_path(json_dict, path)
            nested_class_dict = self._data_service_cache.get_value_dict_from_cache(path)

            value, value_type = nested_json_dict["value"], nested_json_dict["type"]
            class_attr_value_type = nested_class_dict.get("type", None)

            if class_attr_value_type == value_type:
                if self.__is_loadable_state_attribute(path):
                    self.set_service_attribute_value_by_path(path, value)
            else:
                logger.info(
                    "Attribute type of '%s' changed from '%s' to "
                    "'%s'. Ignoring value from JSON file...",
                    path,
                    value_type,
                    class_attr_value_type,
                )

    def _get_state_dict_from_json_file(self) -> dict[str, Any]:
        if self.filename is not None and os.path.exists(self.filename):
            with open(self.filename) as f:
                # Load JSON data from file and update class attributes with these
                # values
                return cast(dict[str, Any], json.load(f))
        return {}

    def set_service_attribute_value_by_path(
        self,
        path: str,
        value: Any,
    ) -> None:
        """
        Sets the value of an attribute in the service managed by the `StateManager`
        given its path as a dot-separated string.

        This method updates the attribute specified by 'path' with 'value' only if the
        attribute is not read-only and the new value differs from the current one.
        It also handles type-specific conversions for the new value before setting it.

        Args:
            path: A dot-separated string indicating the hierarchical path to the
                attribute.
            value: The new value to set for the attribute.
        """

        current_value_dict = get_nested_dict_by_path(self.cache, path)

        # This will also filter out methods as they are 'read-only'
        if current_value_dict["readonly"]:
            logger.debug("Attribute '%s' is read-only. Ignoring new value...", path)
            return

        converted_value = self.__convert_value_if_needed(value, current_value_dict)

        # only set value when it has changed
        if self.__attr_value_has_changed(converted_value, current_value_dict["value"]):
            self.__update_attribute_by_path(path, converted_value)
        else:
            logger.debug("Value of attribute '%s' has not changed...", path)

    def __attr_value_has_changed(self, value_object: Any, current_value: Any) -> bool:
        """Check if the serialized value of `value_object` differs from `current_value`.

        The method serializes `value_object` to compare it, which is mainly
        necessary for handling Quantity objects.
        """

        return dump(value_object)["value"] != current_value

    def __convert_value_if_needed(
        self, value: Any, current_value_dict: dict[str, Any]
    ) -> Any:
        if current_value_dict["type"] == "Quantity":
            return u.convert_to_quantity(value, current_value_dict["value"]["unit"])
        if current_value_dict["type"] == "float" and not isinstance(value, float):
            return float(value)
        return value

    def __update_attribute_by_path(self, path: str, value: Any) -> None:
        parent_path_list, attr_name = path.split(".")[:-1], path.split(".")[-1]

        # If attr_name corresponds to a list entry, extract the attr_name and the
        # index
        attr_name, index = parse_list_attr_and_index(attr_name)

        # Update path to reflect the attribute without list indices
        path = ".".join([*parent_path_list, attr_name])

        attr_cache_type = get_nested_dict_by_path(self.cache, path)["type"]

        # Traverse the object according to the path parts
        target_obj = get_object_attr_from_path_list(self.service, parent_path_list)

        if attr_cache_type in ("ColouredEnum", "Enum"):
            enum_attr = get_object_attr_from_path_list(target_obj, [attr_name])
            setattr(target_obj, attr_name, enum_attr.__class__[value])
        elif attr_cache_type == "list":
            list_obj = get_object_attr_from_path_list(target_obj, [attr_name])
            list_obj[index] = value
        else:
            setattr(target_obj, attr_name, value)

    def __is_loadable_state_attribute(self, property_path: str) -> bool:
        """Checks if an attribute defined by a dot-separated path should be loaded from
        storage.

        For properties, it verifies the presence of the '@load_state' decorator. Regular
        attributes default to being loadable.
        """

        parent_object = get_object_attr_from_path_list(
            self.service, property_path.split(".")[:-1]
        )
        attr_name = property_path.split(".")[-1]

        prop = getattr(type(parent_object), attr_name, None)

        if isinstance(prop, property):
            has_decorator = has_load_state_decorator(prop)
            if not has_decorator:
                logger.debug(
                    "Property '%s' has no '@load_state' decorator. "
                    "Ignoring value from JSON file...",
                    attr_name,
                )
            return has_decorator
        return True
