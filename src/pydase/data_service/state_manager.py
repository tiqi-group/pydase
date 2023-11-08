import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, cast

import pydase.units as u
from pydase.data_service.data_service import process_callable_attribute
from pydase.data_service.data_service_cache import DataServiceCache
from pydase.utils.helpers import (
    get_object_attr_from_path,
    is_property_attribute,
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

    def __init__(self, service: "DataService", filename: Optional[str | Path] = None):
        self.filename = getattr(service, "_filename", None)

        if filename is not None:
            if self.filename is not None:
                logger.warning(
                    f"Overwriting filename {self.filename!r} with {filename!r}."
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
            logger.error(
                "State manager was not initialised with a filename. Skipping "
                "'save_state'..."
            )

    def load_state(self) -> None:
        """
        Loads the DataService's state from a JSON file defined by `self.filename`.
        Updates the service's attributes, respecting type and read-only constraints.
        """

        # Traverse the serialized representation and set the attributes of the class
        json_dict = self._get_state_dict_from_JSON_file()
        if json_dict == {}:
            logger.debug("Could not load the service state.")
            return

        serialized_class = self.cache
        for path in generate_serialized_data_paths(json_dict):
            nested_json_dict = get_nested_dict_by_path(json_dict, path)
            nested_class_dict = get_nested_dict_by_path(serialized_class, path)

            value, value_type = nested_json_dict["value"], nested_json_dict["type"]
            class_attr_value_type = nested_class_dict.get("type", None)

            if class_attr_value_type == value_type:
                self.set_service_attribute_value_by_path(path, value)
            else:
                logger.info(
                    f"Attribute type of {path!r} changed from {value_type!r} to "
                    f"{class_attr_value_type!r}. Ignoring value from JSON file..."
                )

    def _get_state_dict_from_JSON_file(self) -> dict[str, Any]:
        if self.filename is not None:
            # Check if the file specified by the filename exists
            if os.path.exists(self.filename):
                with open(self.filename, "r") as f:
                    # Load JSON data from file and update class attributes with these
                    # values
                    return cast(dict[str, Any], json.load(f))
        return {}

    def set_service_attribute_value_by_path(
        self,
        path: str,
        value: Any,
    ) -> None:
        current_value_dict = get_nested_dict_by_path(self.cache, path)

        if current_value_dict["readonly"]:
            logger.debug(
                f"Attribute {path!r} is read-only. Ignoring value from JSON " "file..."
            )
            return

        converted_value = self.__convert_value_if_needed(value, current_value_dict)

        # only set value when it has changed
        if self.__attr_value_has_changed(converted_value, current_value_dict["value"]):
            self.__update_attribute_by_path(path, converted_value)
        else:
            logger.debug(f"Value of attribute {path!r} has not changed...")

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
        return value

    def __update_attribute_by_path(self, path: str, value: Any) -> None:
        parent_path_list, attr_name = path.split(".")[:-1], path.split(".")[-1]

        # If attr_name corresponds to a list entry, extract the attr_name and the
        # index
        attr_name, index = parse_list_attr_and_index(attr_name)

        # Traverse the object according to the path parts
        target_obj = get_object_attr_from_path(self.service, parent_path_list)

        # If the attribute is a property, change it using the setter without getting
        # the property value (would otherwise be bad for expensive getter methods)
        if is_property_attribute(target_obj, attr_name):
            setattr(target_obj, attr_name, value)
            return

        attr = get_object_attr_from_path(target_obj, [attr_name])
        if attr is None:
            # If the attribute does not exist, abort setting the value. An error
            # message has already been logged.
            # This will never happen as this function is only called when the
            # attribute exists in the cache.
            return

        if isinstance(attr, Enum):
            setattr(target_obj, attr_name, attr.__class__[value])
        elif isinstance(attr, list) and index is not None:
            attr[index] = value
        elif callable(attr):
            process_callable_attribute(attr, value["args"])
        else:
            setattr(target_obj, attr_name, value)
