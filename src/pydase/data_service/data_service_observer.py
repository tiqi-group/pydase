import logging
from copy import copy
from typing import TYPE_CHECKING, Any

from pydase.data_service.state_manager import StateManager
from pydase.observer_pattern.observable.observable import Observable
from pydase.observer_pattern.observer.observer import Observer
from pydase.observer_pattern.observer.property_observer import (
    get_property_dependencies,
    reverse_dict,
)
from pydase.utils.helpers import get_object_attr_from_path_list

if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


class DataServiceObserver(Observer):
    def __init__(self, state_manager: StateManager) -> None:
        super().__init__(state_manager.service)
        self.initialised = False
        self.state_manager = state_manager
        self.changing_attributes: list[str] = []
        self.property_deps_dict = reverse_dict(
            self._get_properties_and_their_dependencies(self.observable)
        )
        self._change_callbacks: list[Callable[[str, Any, dict[str, Any]], None]] = []
        self.initialised = True

    def on_change(self, full_access_path: str, value: Any) -> None:
        if not self.initialised:
            return

        if full_access_path in self.changing_attributes:
            self.changing_attributes.remove(full_access_path)

        cached_value_dict = copy(
            self.state_manager._data_service_cache.get_value_dict_from_cache(
                full_access_path
            )
        )

        cached_value = cached_value_dict.get("value")
        if cached_value != value:
            logger.debug("'%s' changed to '%s'", full_access_path, value)

        self._update_cache_value(full_access_path, cached_value_dict, value)

        for callback in self._change_callbacks:
            callback(full_access_path, value, cached_value_dict)

        self._notify_dependent_property_changes(full_access_path)

    def _update_cache_value(
        self, full_access_path: str, cached_value_dict: dict[str, Any], value: Any
    ) -> None:
        if cached_value_dict != {}:
            self.state_manager._data_service_cache.update_cache(
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
                    get_object_attr_from_path_list(self.observable, prop.split(".")),
                )

    def on_change_start(self, full_access_path: str) -> None:
        self.changing_attributes.append(full_access_path)

    def _get_properties_and_their_dependencies(
        self, obj: Observable, prefix: str = ""
    ) -> dict[str, list[str]]:
        deps = {}
        for k, value in vars(type(obj)).items():
            prefix = (
                f"{prefix}." if prefix != "" and not prefix.endswith(".") else prefix
            )
            key = f"{prefix}{k}"
            if isinstance(value, property):
                deps[key] = get_property_dependencies(value, prefix)

        for k, value in vars(obj).items():
            prefix = (
                f"{prefix}." if prefix != "" and not prefix.endswith(".") else prefix
            )
            key = f"{prefix}{k}"
            if isinstance(value, Observable):
                new_prefix = f"{key}."
                deps.update(
                    self._get_properties_and_their_dependencies(value, new_prefix)
                )
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, Observable):
                        new_prefix = f"{key}[{i}]"
                        deps.update(
                            self._get_properties_and_their_dependencies(
                                item, new_prefix
                            )
                        )
            elif isinstance(value, dict):
                for key, val in value.items():
                    if isinstance(val, Observable):
                        new_prefix = f"{key}['{key}']"
                        deps.update(
                            self._get_properties_and_their_dependencies(val, new_prefix)
                        )

        return deps

    def _get_property_values(
        self, obj: Observable, prefix: str = ""
    ) -> dict[str, list[str]]:
        values = {}
        for k, value in vars(type(obj)).items():
            key = f"{prefix}{k}"
            if isinstance(value, property):
                values[key] = getattr(obj, k)

        for k, value in vars(obj).items():
            key = f"{prefix}{k}"
            if isinstance(value, Observable):
                new_prefix = f"{key}." if not key.endswith("]") else key
                values.update(self._get_property_values(value, new_prefix))
        return values
