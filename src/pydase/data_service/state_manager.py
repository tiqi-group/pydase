import asyncio
import contextlib
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from pydase.data_service.data_service_cache import DataServiceCache
from pydase.utils.helpers import (
    get_object_by_path_parts,
    is_property_attribute,
    parse_full_access_path,
    parse_serialized_key,
)
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.serializer import (
    SerializationPathError,
    generate_serialized_data_paths,
    get_nested_dict_by_path,
    serialized_dict_is_nested_object,
)
from pydase.utils.serialization.types import SerializedObject

if TYPE_CHECKING:
    from pydase import DataService

logger = logging.getLogger(__name__)


def load_state(func: Callable[..., Any]) -> Callable[..., Any]:
    """This function should be used as a decorator on property setters to indicate that
    the value should be loaded from the JSON file.

    Example:
        ```python
        class Service(pydase.DataService):
            _name = "Service"

            @property
            def name(self) -> str:
                return self._name

            @name.setter
            @load_state
            def name(self, value: str) -> None:
                self._name = value
        ```
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
    persistence layer. It provides fast access to the most recently known state of the
    service and ensures consistent state updates across connected clients and service
    restarts.

    The StateManager is used by the web server to apply updates to service attributes
    and to serve the current state to newly connected clients. Internally, it creates a
    [`DataServiceCache`][pydase.data_service.data_service_cache.DataServiceCache]
    instance to track the state of public attributes and properties.

    The StateManager also handles state persistence: it can load a previously saved
    state from disk at startup and periodically autosave the current state to a file
    during runtime.

    Args:
        service: The DataService instance whose state is being managed.
        filename: The file name used for loading and storing the DataService's state.
            If provided, the state is loaded from this file at startup and saved to it
            on shutdown or at regular intervals.
        autosave_interval: Interval in seconds between automatic state save events.
            If set to `None`, automatic saving is disabled.

    Note:
        The StateManager does not autonomously poll hardware state. It relies on the
        service to perform such updates. The cache maintained by
        [`DataServiceCache`][pydase.data_service.data_service_cache.DataServiceCache]
        reflects the last known state as notified by the `DataServiceObserver`, and is
        used by the web interface to provide fast and accurate state rendering for
        connected clients.
    """

    def __init__(
        self,
        service: "DataService",
        filename: str | Path | None = None,
        autosave_interval: float | None = None,
    ) -> None:
        self.filename = getattr(service, "_filename", None)

        if filename is not None:
            if self.filename is not None:
                logger.warning(
                    "Overwriting filename '%s' with '%s'.", self.filename, filename
                )
            self.filename = filename

        self.service = service
        self.cache_manager = DataServiceCache(self.service)
        self.autosave_interval = autosave_interval

    async def autosave(self) -> None:
        """Periodically saves the current service state to the configured file.

        This coroutine is automatically started by the [`pydase.Server`][pydase.Server]
        when a filename is provided. It runs in the background and writes the latest
        known state of the service to disk every `autosave_interval` seconds.

        If `autosave_interval` is set to `None`, autosaving is disabled and this
        coroutine exits immediately.
        """

        if self.autosave_interval is None:
            return

        while True:
            try:
                if self.filename is not None:
                    self.save_state()
                await asyncio.sleep(self.autosave_interval)
            except Exception as e:
                logger.exception(e)

    @property
    def cache_value(self) -> dict[str, SerializedObject]:
        """Returns the "value" value of the DataService serialization."""
        return cast("dict[str, SerializedObject]", self.cache_manager.cache["value"])

    def save_state(self) -> None:
        """Saves the DataService's current state to a JSON file defined by
        `self.filename`.
        """

        if self.filename is not None:
            with open(self.filename, "w") as f:
                json.dump(self.cache_value, f, indent=4)
        else:
            logger.debug(
                "State manager was not initialised with a filename. Skipping "
                "'save_state'..."
            )

    def load_state(self) -> None:
        """Loads the DataService's state from a JSON file defined by `self.filename`.
        Updates the service's attributes, respecting type and read-only constraints.
        """

        # Traverse the serialized representation and set the attributes of the class
        json_dict = self._get_state_dict_from_json_file()
        if json_dict == {}:
            logger.debug("Could not load the service state.")
            return

        for path in generate_serialized_data_paths(json_dict):
            if self.__is_loadable_state_attribute(path):
                nested_json_dict = get_nested_dict_by_path(json_dict, path)
                try:
                    nested_class_dict = self.cache_manager.get_value_dict_from_cache(
                        path
                    )
                except (SerializationPathError, KeyError):
                    nested_class_dict = {
                        "full_access_path": path,
                        "value": None,
                        "type": "None",
                        "doc": None,
                        "readonly": False,
                    }

                value_type = nested_json_dict["type"]
                class_attr_value_type = nested_class_dict.get("type", None)

                if class_attr_value_type == value_type:
                    self.set_service_attribute_value_by_path(path, nested_json_dict)
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
                return cast("dict[str, Any]", json.load(f))
        return {}

    def set_service_attribute_value_by_path(
        self,
        path: str,
        serialized_value: SerializedObject,
    ) -> None:
        """Sets the value of an attribute in the service managed by the `StateManager`
        given its path as a dot-separated string.

        This method updates the attribute specified by 'path' with 'value' only if the
        attribute is not read-only and the new value differs from the current one.
        It also handles type-specific conversions for the new value before setting it.

        Args:
            path:
                A dot-separated string indicating the hierarchical path to the
                attribute.
            serialized_value:
                The serialized representation of the new value to set for the attribute.
        """

        try:
            current_value_dict = self.cache_manager.get_value_dict_from_cache(path)
        except (SerializationPathError, KeyError):
            current_value_dict = {
                "full_access_path": path,
                "value": None,
                "type": "None",
                "doc": None,
                "readonly": False,
            }

        if "full_access_path" not in serialized_value:
            # Backwards compatibility for JSON files not containing the
            # full_access_path
            logger.warning(
                "The format of your JSON file is out-of-date. This might lead "
                "to unexpected errors. Please consider updating it."
            )
            serialized_value["full_access_path"] = current_value_dict[
                "full_access_path"
            ]

        # only set value when it has changed
        if self.__attr_value_has_changed(serialized_value, current_value_dict):
            self.__update_attribute_by_path(path, serialized_value)
        else:
            logger.debug("Value of attribute '%s' has not changed...", path)

    def __attr_value_has_changed(
        self, serialized_new_value: Any, serialized_current_value: Any
    ) -> bool:
        return not (
            serialized_new_value["type"] == serialized_current_value["type"]
            and serialized_new_value["value"] == serialized_current_value["value"]
        )

    def __update_attribute_by_path(
        self, path: str, serialized_value: SerializedObject
    ) -> None:
        is_value_set = False
        path_parts = parse_full_access_path(path)
        target_obj = get_object_by_path_parts(self.service, path_parts[:-1])

        if self.__cached_value_is_enum(path):
            enum_attr = get_object_by_path_parts(target_obj, [path_parts[-1]])
            # take the value of the existing enum class
            if serialized_value["type"] in ("ColouredEnum", "Enum"):
                # This error will arise when setting an enum from another enum class.
                # In this case, we resort to loading the enum and setting it directly.
                with contextlib.suppress(KeyError):
                    value = enum_attr.__class__[serialized_value["value"]]
                    is_value_set = True

        if not is_value_set:
            value = loads(serialized_value)

        # set the value
        if isinstance(target_obj, list | dict):
            processed_key = parse_serialized_key(path_parts[-1])
            target_obj[processed_key] = value  # type: ignore
        else:
            # Don't allow adding attributes to objects through state manager
            if self.__attr_exists_on_target_obj(
                target_obj=target_obj, name=path_parts[-1]
            ):
                raise AttributeError(
                    f"{target_obj.__class__.__name__!r} object has no attribute "
                    f"{path_parts[-1]!r}"
                )

            setattr(target_obj, path_parts[-1], value)

    def __is_loadable_state_attribute(self, full_access_path: str) -> bool:
        """Checks if an attribute defined by a dot-separated path should be loaded from
        storage.

        For properties, it verifies the presence of the '@load_state' decorator. Regular
        attributes default to being loadable.
        """

        path_parts = parse_full_access_path(full_access_path)
        parent_object = get_object_by_path_parts(self.service, path_parts[:-1])

        if is_property_attribute(parent_object, path_parts[-1]):
            prop = getattr(type(parent_object), path_parts[-1])
            has_decorator = has_load_state_decorator(prop)
            if not has_decorator:
                logger.debug(
                    "Property '%s' has no '@load_state' decorator. "
                    "Ignoring value from JSON file...",
                    path_parts[-1],
                )
            return has_decorator

        try:
            cached_serialization_dict = self.cache_manager.get_value_dict_from_cache(
                full_access_path
            )

            if cached_serialization_dict["value"] == "method":
                return False

            # nested objects cannot be loaded
            return not serialized_dict_is_nested_object(cached_serialization_dict)
        except SerializationPathError:
            logger.debug(
                "Path %a could not be loaded. It does not correspond to an attribute of"
                " the class. Ignoring value from JSON file...",
                path_parts[-1],
            )
            return False

    def __cached_value_is_enum(self, path: str) -> bool:
        try:
            attr_cache_type = self.cache_manager.get_value_dict_from_cache(path)["type"]

            return attr_cache_type in ("ColouredEnum", "Enum")
        except Exception:
            return False

    def __attr_exists_on_target_obj(self, target_obj: Any, name: str) -> bool:
        return not is_property_attribute(target_obj, name) and not hasattr(
            target_obj, name
        )
