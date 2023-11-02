import json
import logging
import os
from typing import TYPE_CHECKING, Any, cast

import pydase.units as u
from pydase.utils.helpers import (
    generate_paths_from_DataService_dict,
    get_nested_value_from_DataService_by_path_and_key,
    set_nested_value_in_dict,
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

    def __init__(self, service: "DataService"):
        self.cache: dict[str, Any] = {}  # Initialize an empty cache
        self.filename = service._filename
        self.service = service
        self.service._callback_manager.add_notification_callback(self.update_cache)

    def update_cache(self, parent_path: str, name: str, value: Any) -> None:
        # Remove the part before the first "." in the parent_path
        parent_path = ".".join(parent_path.split(".")[1:])

        # Construct the full path
        full_path = f"{parent_path}.{name}" if parent_path else name

        set_nested_value_in_dict(self.cache, full_path, value)

    def save_state(self) -> None:
        """
        Serialize the DataService instance and write it to a JSON file.

        Args:
            filename (str): The name of the file to write to.
        """
        if self.filename is not None:
            with open(self.filename, "w") as f:
                json.dump(self.cache, f, indent=4)
        else:
            logger.error(
                f"Class {self.__class__.__name__} was not initialised with a filename. "
                'Skipping "write_to_file"...'
            )

    def load_state(self) -> None:
        # Traverse the serialized representation and set the attributes of the class
        if self.cache == {}:
            self.cache = self.service.serialize()

        json_dict = self._load_state_from_file()
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

                self.service.update_DataService_attribute(parts[:-1], attr_name, value)
            else:
                logger.info(
                    f'Attribute type of "{path}" changed from "{value_type}" to '
                    f'"{class_value_type}". Ignoring value from JSON file...'
                )

    def _load_state_from_file(self) -> dict[str, Any]:
        if self.filename is not None:
            # Check if the file specified by the filename exists
            if os.path.exists(self.filename):
                with open(self.filename, "r") as f:
                    # Load JSON data from file and update class attributes with these
                    # values
                    return cast(dict[str, Any], json.load(f))
        return {}
