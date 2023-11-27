import inspect
import logging
import re
from typing import Any

from pydase.observer_pattern.observable.observable import Observable
from pydase.observer_pattern.observer.observer import Observer
from pydase.utils.helpers import get_object_attr_from_path_list

logger = logging.getLogger(__name__)


def reverse_dict(original_dict: dict[str, list[str]]) -> dict[str, list[str]]:
    reversed_dict: dict[str, list[str]] = {
        value: [] for values in original_dict.values() for value in values
    }
    for key, values in original_dict.items():
        for value in values:
            reversed_dict[value].append(key)
    return reversed_dict


def get_property_dependencies(prop: property, prefix: str = "") -> list[str]:
    source_code_string = inspect.getsource(prop.fget)  # type: ignore[arg-type, reportGeneralTypeIssues]
    pattern = r"self\.([^\s\{\}]+)"
    matches = re.findall(pattern, source_code_string)
    return [prefix + match for match in matches if "(" not in match]


class PropertyObserver(Observer):
    def __init__(self, observable: Observable) -> None:
        super().__init__(observable)
        self.initialised = False
        self.changing_attributes: list[str] = []
        self.property_deps_dict = reverse_dict(
            self._get_properties_and_their_dependencies(self.observable)
        )
        self.property_values = self._get_property_values(self.observable)
        self.initialised = True

    def on_change(self, full_access_path: str, value: Any) -> None:
        if full_access_path in self.changing_attributes:
            self.changing_attributes.remove(full_access_path)

        if (
            not self.initialised
            or self.property_values.get(full_access_path, None) == value
        ):
            return

        logger.info("'%s' changed to '%s'", full_access_path, value)
        if full_access_path in self.property_values:
            self.property_values[full_access_path] = value

        changed_props = self.property_deps_dict.get(full_access_path, [])
        for prop in changed_props:
            if prop not in self.changing_attributes:
                self._notify_changed(
                    prop,
                    get_object_attr_from_path_list(self.observable, prop.split(".")),
                )

    def on_change_start(self, full_access_path: str) -> None:
        self.changing_attributes.append(full_access_path)
        logger.info("'%s' is being changed", full_access_path)

    def _get_properties_and_their_dependencies(
        self, obj: Observable, prefix: str = ""
    ) -> dict[str, list[str]]:
        deps = {}
        for k, value in vars(type(obj)).items():
            key = f"{prefix}{k}"
            if isinstance(value, property):
                deps[key] = get_property_dependencies(value, prefix)

        for k, value in vars(obj).items():
            key = f"{prefix}{k}"
            if isinstance(value, Observable):
                new_prefix = f"{key}." if not key.endswith("]") else key
                deps.update(
                    self._get_properties_and_their_dependencies(value, new_prefix)
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
