import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar, SupportsIndex

if TYPE_CHECKING:
    from pydase.observer_pattern.observer.observer import Observer

logger = logging.getLogger(__name__)


class ObservableObject(ABC):
    _list_mapping: ClassVar[dict[int, "_ObservableList"]] = {}
    _dict_mapping: ClassVar[dict[int, "_ObservableDict"]] = {}

    def __init__(self) -> None:
        if not hasattr(self, "_observers"):
            self._observers: dict[str, list["ObservableObject | Observer"]] = {}

    def add_observer(
        self, observer: "ObservableObject | Observer", attr_name: str = ""
    ) -> None:
        if attr_name not in self._observers:
            self._observers[attr_name] = []
        if observer not in self._observers[attr_name]:
            self._observers[attr_name].append(observer)

    def _remove_observer(self, observer: "ObservableObject", attribute: str) -> None:
        if attribute in self._observers:
            self._observers[attribute].remove(observer)

    @abstractmethod
    def _remove_observer_if_observable(self, name: str) -> None:
        """Removes the current object as an observer from an observable attribute.

        This method is called before an attribute of the observable object is
        changed. If the current value of the attribute is an instance of
        `ObservableObject`, this method removes the current object from its list
        of observers. This is a crucial step to avoid unwanted notifications from
        the old value of the attribute.
        """

    def _notify_changed(self, changed_attribute: str, value: Any) -> None:
        """Notifies all observers about changes to an attribute.

        This method iterates through all observers registered for the object and
        invokes their notification method. It is called whenever an attribute of
        the observable object is changed.

        Args:
            changed_attribute (str): The name of the changed attribute.
            value (Any): The value that the attribute was set to.
        """
        for attr_name, observer_list in self._observers.items():
            for observer in observer_list:
                extendend_attr_path = self._construct_extended_attr_path(
                    attr_name, changed_attribute
                )
                observer._notify_changed(extendend_attr_path, value)

    def _notify_change_start(self, changing_attribute: str) -> None:
        """Notify observers that an attribute or item change process has started.

        This method is called at the start of the process of modifying an attribute in
        the observed `Observable` object. It registers the attribute as currently
        undergoing a change. This registration helps in managing and tracking changes as
        they occur, especially in scenarios where the order of changes or their state
        during the transition is significant.

        Args:
            changing_attribute (str): The name of the attribute that is starting to
            change. This is typically the full access path of the attribute in the
            `Observable`.
            value (Any): The value that the attribute is being set to.
        """

        for attr_name, observer_list in self._observers.items():
            for observer in observer_list:
                extended_attr_path = self._construct_extended_attr_path(
                    attr_name, changing_attribute
                )
                observer._notify_change_start(extended_attr_path)

    def _initialise_new_objects(self, attr_name_or_key: Any, value: Any) -> Any:
        new_value = value
        if isinstance(value, list):
            if id(value) in self._list_mapping:
                # If the list `value` was already referenced somewhere else
                new_value = self._list_mapping[id(value)]
            else:
                # convert the builtin list into a ObservableList
                new_value = _ObservableList(original_list=value)
                self._list_mapping[id(value)] = new_value
        elif isinstance(value, dict):
            if id(value) in self._dict_mapping:
                # If the list `value` was already referenced somewhere else
                new_value = self._dict_mapping[id(value)]
            else:
                # convert the builtin list into a ObservableList
                new_value = _ObservableDict(original_dict=value)
                self._dict_mapping[id(value)] = new_value
        if isinstance(new_value, ObservableObject):
            new_value.add_observer(self, str(attr_name_or_key))
        return new_value

    @abstractmethod
    def _construct_extended_attr_path(
        self, observer_attr_name: str, instance_attr_name: str
    ) -> str:
        """
        Constructs the extended attribute path for notification purposes, which is used
        in the observer pattern to specify the full path of an observed attribute.

        This abstract method is implemented by the classes inheriting from
        `ObservableObject`.

        Args:
            observer_attr_name (str): The name of the attribute in the observer that
            holds a reference to the instance. Equals `""` if observer itself is of type
            `Observer`.
            instance_attr_name (str): The name of the attribute within the instance that
            has changed.

        Returns:
            str: The constructed extended attribute path.
        """


class _ObservableList(ObservableObject, list[Any]):
    def __init__(
        self,
        original_list: list[Any],
    ) -> None:
        self._original_list = original_list
        ObservableObject.__init__(self)
        list.__init__(self, self._original_list)
        for i, item in enumerate(self._original_list):
            super().__setitem__(i, self._initialise_new_objects(f"[{i}]", item))

    def __setitem__(self, key: int, value: Any) -> None:  # type: ignore[override]
        if hasattr(self, "_observers"):
            self._remove_observer_if_observable(f"[{key}]")
            value = self._initialise_new_objects(f"[{key}]", value)
            self._notify_change_start(f"[{key}]")

        super().__setitem__(key, value)

        self._notify_changed(f"[{key}]", value)

    def append(self, __object: Any) -> None:
        self._initialise_new_objects(f"[{len(self)}]", __object)
        super().append(__object)
        self._notify_changed("", self)

    def clear(self) -> None:
        self._remove_self_from_observables()

        super().clear()

        self._notify_changed("", self)

    def extend(self, __iterable: Iterable[Any]) -> None:
        self._remove_self_from_observables()

        try:
            super().extend(__iterable)
        finally:
            for i, item in enumerate(self):
                super().__setitem__(i, self._initialise_new_objects(f"[{i}]", item))

            self._notify_changed("", self)

    def insert(self, __index: SupportsIndex, __object: Any) -> None:
        self._remove_self_from_observables()

        try:
            super().insert(__index, __object)
        finally:
            for i, item in enumerate(self):
                super().__setitem__(i, self._initialise_new_objects(f"[{i}]", item))

            self._notify_changed("", self)

    def pop(self, __index: SupportsIndex = -1) -> Any:
        self._remove_self_from_observables()

        try:
            popped_item = super().pop(__index)
        finally:
            for i, item in enumerate(self):
                super().__setitem__(i, self._initialise_new_objects(f"[{i}]", item))

            self._notify_changed("", self)
        return popped_item

    def remove(self, __value: Any) -> None:
        self._remove_self_from_observables()

        try:
            super().remove(__value)
        finally:
            for i, item in enumerate(self):
                super().__setitem__(i, self._initialise_new_objects(f"[{i}]", item))

            self._notify_changed("", self)

    def _remove_self_from_observables(self) -> None:
        for i in range(len(self)):
            self._remove_observer_if_observable(f"[{i}]")

    def _remove_observer_if_observable(self, name: str) -> None:
        key = int(name[1:-1])
        current_value = self.__getitem__(key)

        if isinstance(current_value, ObservableObject):
            current_value._remove_observer(self, name)

    def _construct_extended_attr_path(
        self, observer_attr_name: str, instance_attr_name: str
    ) -> str:
        if observer_attr_name != "":
            return f"{observer_attr_name}{instance_attr_name}"
        return instance_attr_name


class _ObservableDict(dict[str, Any], ObservableObject):
    def __init__(
        self,
        original_dict: dict[str, Any],
    ) -> None:
        self._original_dict = original_dict
        ObservableObject.__init__(self)
        dict.__init__(self)
        for key, value in self._original_dict.items():
            super().__setitem__(key, self._initialise_new_objects(f"['{key}']", value))

    def __setitem__(self, key: str, value: Any) -> None:
        if not isinstance(key, str):
            logger.warning("Converting non-string dictionary key %s to string.", key)
            key = str(key)

        if hasattr(self, "_observers"):
            self._remove_observer_if_observable(f"['{key}']")
            value = self._initialise_new_objects(key, value)
            self._notify_change_start(f"['{key}']")

        super().__setitem__(key, value)

        self._notify_changed(f"['{key}']", value)

    def _remove_observer_if_observable(self, name: str) -> None:
        key = name[2:-2]
        current_value = self.get(key, None)

        if isinstance(current_value, ObservableObject):
            current_value._remove_observer(self, name)

    def _construct_extended_attr_path(
        self, observer_attr_name: str, instance_attr_name: str
    ) -> str:
        if observer_attr_name != "":
            return f"{observer_attr_name}{instance_attr_name}"
        return instance_attr_name
