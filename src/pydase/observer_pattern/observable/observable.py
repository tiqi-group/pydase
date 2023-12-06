import logging
from typing import Any

from pydase.observer_pattern.observable.observable_object import ObservableObject
from pydase.utils.helpers import is_property_attribute

logger = logging.getLogger(__name__)


class Observable(ObservableObject):
    def __init__(self) -> None:
        super().__init__()
        class_attrs = {
            k: type(self).__dict__[k]
            for k in set(type(self).__dict__)
            - set(Observable.__dict__)
            - set(self.__dict__)
        }
        for name, value in class_attrs.items():
            if isinstance(value, property) or callable(value):
                continue
            self.__dict__[name] = self._initialise_new_objects(name, value)

    def __setattr__(self, name: str, value: Any) -> None:
        if not hasattr(self, "_observers") and name != "_observers":
            logger.warning(
                "Ensure that super().__init__() is called at the start of the '%s' "
                "constructor! Failing to do so may lead to unexpected behavior.",
                type(self).__name__,
            )
            self._observers = {}

        value = self._handle_observable_setattr(name, value)

        super().__setattr__(name, value)

        self._notify_changed(name, value)

    def __getattribute__(self, name: str) -> Any:
        if is_property_attribute(self, name):
            self._notify_change_start(name)

        value = super().__getattribute__(name)

        if is_property_attribute(self, name):
            self._notify_changed(name, value)

        return value

    def _handle_observable_setattr(self, name: str, value: Any) -> Any:
        if name == "_observers":
            return value

        self._remove_observer_if_observable(name)
        value = self._initialise_new_objects(name, value)
        self._notify_change_start(name)
        return value

    def _remove_observer_if_observable(self, name: str) -> None:
        if not is_property_attribute(self, name):
            current_value = getattr(self, name, None)

            if isinstance(current_value, ObservableObject):
                current_value._remove_observer(self, name)

    def _construct_extended_attr_path(
        self, observer_attr_name: str, instance_attr_name: str
    ) -> str:
        if observer_attr_name != "":
            return f"{observer_attr_name}.{instance_attr_name}"
        return instance_attr_name
