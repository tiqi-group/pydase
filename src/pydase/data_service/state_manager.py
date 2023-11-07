import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, cast

import pydase.units as u
from pydase.data_service.data_service_cache import DataServiceCache
from pydase.utils.helpers import get_nested_value_from_DataService_by_path_and_key
from pydase.utils.serializer import generate_paths_from_DataService_dict

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
                        f"Attribute {path!r} is read-only. Ignoring value from JSON "
                        "file..."
                    )
                    continue
                # Split the path into parts
                parts = path.split(".")
                attr_name = parts[-1]

                # Convert dictionary into Quantity
                if class_value_type == "Quantity":
                    value = u.convert_to_quantity(value)

                self.service.update_DataService_attribute(parts[:-1], attr_name, value)
            else:
                logger.info(
                    f"Attribute type of {path!r} changed from {value_type!r} to "
                    f"{class_value_type!r}. Ignoring value from JSON file..."
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
