import inspect
import logging
import re
from typing import Any

from pydase.observer_pattern.observable.observable import Observable
from pydase.observer_pattern.observer.observer import Observer
from pydase.utils.helpers import is_descriptor

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
    source_code_string = inspect.getsource(prop.fget)  # type: ignore[arg-type]
    pattern = r"self\.([^\s\{\}\(\)]+)"
    matches = re.findall(pattern, source_code_string)
    return [prefix + match for match in matches if "(" not in match]


class PropertyObserver(Observer):
    def __init__(self, observable: Observable) -> None:
        self.property_deps_dict: dict[str, list[str]] = {}
        super().__init__(observable)
        self._update_property_deps_dict()

    def _update_property_deps_dict(self) -> None:
        self.property_deps_dict = reverse_dict(
            self._get_properties_and_their_dependencies(self.observable)
        )

    def _get_properties_and_their_dependencies(
        self, obj: Observable, prefix: str = ""
    ) -> dict[str, list[str]]:
        deps: dict[str, Any] = {}

        self._process_observable_properties(obj, deps, prefix)
        self._process_nested_observables_properties(obj, deps, prefix)

        return deps

    def _process_observable_properties(
        self, obj: Observable, deps: dict[str, Any], prefix: str
    ) -> None:
        for k, value in inspect.getmembers(type(obj)):
            prefix = (
                f"{prefix}." if prefix != "" and not prefix.endswith(".") else prefix
            )
            key = f"{prefix}{k}"
            if isinstance(value, property):
                deps[key] = get_property_dependencies(value, prefix)

    def _process_nested_observables_properties(
        self, obj: Observable, deps: dict[str, Any], prefix: str
    ) -> None:
        for k, value in {**vars(type(obj)), **vars(obj)}.items():
            actual_value = value
            prefix = (
                f"{prefix}." if prefix != "" and not prefix.endswith(".") else prefix
            )
            parent_path = f"{prefix}{k}"

            # Get value from descriptor
            if not isinstance(value, property) and is_descriptor(value):
                actual_value = getattr(obj, k)

            if isinstance(actual_value, Observable):
                new_prefix = f"{parent_path}."
                deps.update(
                    self._get_properties_and_their_dependencies(
                        actual_value, new_prefix
                    )
                )
            elif isinstance(value, list | dict):
                self._process_collection_item_properties(
                    actual_value, deps, parent_path
                )

    def _process_collection_item_properties(
        self,
        collection: list[Any] | dict[str, Any],
        deps: dict[str, Any],
        parent_path: str,
    ) -> None:
        if isinstance(collection, list):
            for i, item in enumerate(collection):
                if isinstance(item, Observable):
                    new_prefix = f"{parent_path}[{i}]"
                    deps.update(
                        self._get_properties_and_their_dependencies(item, new_prefix)
                    )
        elif isinstance(collection, dict):
            for key, val in collection.items():
                if isinstance(val, Observable):
                    new_prefix = f'{parent_path}["{key}"]'
                    deps.update(
                        self._get_properties_and_their_dependencies(val, new_prefix)
                    )
