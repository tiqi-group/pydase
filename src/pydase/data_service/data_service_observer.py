import logging
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from pydase.data_service.state_manager import StateManager
from pydase.observer_pattern.observable.observable_object import ObservableObject
from pydase.observer_pattern.observer.property_observer import (
    PropertyObserver,
)
from pydase.utils.helpers import (
    get_object_attr_from_path,
)
from pydase.utils.serialization.serializer import (
    SerializationPathError,
    dump,
)
from pydase.utils.serialization.types import SerializedObject

logger = logging.getLogger(__name__)


def _is_nested_attribute(full_access_path: str, changing_attributes: list[str]) -> bool:
    """Return True if the full_access_path is a nested attribute of any
    changing_attribute."""

    return any(
        (
            full_access_path.startswith((f"{attr}.", f"{attr}["))
            and full_access_path != attr
        )
        for attr in changing_attributes
    )


class DataServiceObserver(PropertyObserver):
    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager
        self._notification_callbacks: list[
            Callable[[str, Any, SerializedObject], None]
        ] = []
        super().__init__(state_manager.service)

    def on_change(self, full_access_path: str, value: Any) -> None:
        if _is_nested_attribute(full_access_path, self.changing_attributes):
            return
        cached_value_dict: SerializedObject

        try:
            cached_value_dict = deepcopy(
                self.state_manager.cache_manager.get_value_dict_from_cache(
                    full_access_path
                )
            )
        except (SerializationPathError, KeyError):
            cached_value_dict = {
                "full_access_path": full_access_path,
                "value": None,
                "type": "None",
                "doc": None,
                "readonly": False,
            }

        cached_value = cached_value_dict.get("value")
        if (
            all(part[0] != "_" for part in full_access_path.split("."))
            and cached_value != dump(value)["value"]
        ):
            logger.debug("'%s' changed to '%s'", full_access_path, value)

            self._update_cache_value(full_access_path, value, cached_value_dict)

            cached_value_dict = deepcopy(
                self.state_manager.cache_manager.get_value_dict_from_cache(
                    full_access_path
                )
            )

            for callback in self._notification_callbacks:
                callback(full_access_path, value, cached_value_dict)

        if isinstance(value, ObservableObject):
            self._update_property_deps_dict()

        self._notify_dependent_property_changes(full_access_path)

    def _update_cache_value(
        self,
        full_access_path: str,
        value: Any,
        cached_value_dict: SerializedObject | dict[str, Any],
    ) -> None:
        value_dict = dump(value)
        if (
            cached_value_dict != {}
            and cached_value_dict["type"] != "method"
            and cached_value_dict["type"] != value_dict["type"]
        ):
            logger.warning(
                "Type of '%s' changed from '%s' to '%s'. This could have unwanted "
                "side effects! Consider setting it to '%s' directly.",
                full_access_path,
                cached_value_dict["type"],
                value_dict["type"],
                cached_value_dict["type"],
            )
        self.state_manager.cache_manager.update_cache(
            full_access_path,
            value,
        )

    def _notify_dependent_property_changes(self, changed_attr_path: str) -> None:
        changed_props = self.property_deps_dict.get(changed_attr_path, [])
        for prop in changed_props:
            # only notify about changing attribute if it is not currently being
            # "changed" e.g. when calling the getter of a property within another
            # property
            if prop not in self.changing_attributes:
                self._notify_changed(
                    prop,
                    get_object_attr_from_path(self.observable, prop),
                )

    def add_notification_callback(
        self, callback: Callable[[str, Any, SerializedObject], None]
    ) -> None:
        """
        Registers a callback function to be invoked upon attribute changes in the
        observed object.

        This method allows for the addition of custom callback functions that will be
        executed whenever there is a change in the value of an observed attribute. The
        callback function is called with detailed information about the change, enabling
        external logic to respond to specific state changes within the observable
        object.

        Args:
            callback:
                The callback function to be registered. The function should have the
                following signature:

                - full_access_path (str): The full dot-notation access path of the
                  changed attribute. This path indicates the location of the changed
                  attribute within the observable object's structure.
                - value (Any): The new value of the changed attribute.
                - cached_value_dict (dict[str, Any]): A dictionary representing the
                  cached state of the attribute prior to the change. This can be useful
                  for understanding the nature of the change and for historical
                  comparison.
        """
        self._notification_callbacks.append(callback)
