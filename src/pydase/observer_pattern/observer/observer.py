import logging
from abc import ABC, abstractmethod
from typing import Any

from pydase.observer_pattern.observable import Observable

logger = logging.getLogger(__name__)


class Observer(ABC):
    def __init__(self, observable: Observable) -> None:
        self.observable = observable
        self.observable.add_observer(self)
        self.changing_attributes: list[str] = []

    def _notify_changed(self, changed_attribute: str, value: Any) -> None:
        self.on_change(full_access_path=changed_attribute, value=value)

        if changed_attribute in self.changing_attributes:
            self.changing_attributes.remove(changed_attribute)

    def _notify_change_start(self, changing_attribute: str) -> None:
        self.changing_attributes.append(changing_attribute)
        self.on_change_start(changing_attribute)

    @abstractmethod
    def on_change(self, full_access_path: str, value: Any) -> None: ...

    def on_change_start(self, full_access_path: str) -> None:
        return
