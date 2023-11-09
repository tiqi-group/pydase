from collections.abc import Callable
from typing import Any

import pydase.units as u
from pydase.utils.warnings import (
    warn_if_instance_class_does_not_inherit_from_DataService,
)


class DataServiceList(list):
    """
    DataServiceList is a list with additional functionality to trigger callbacks
    whenever an item is set. This can be used to track changes in the list items.

    The class takes the same arguments as the list superclass during initialization,
    with an additional optional 'callback' argument that is a list of functions.
    These callbacks are stored and executed whenever an item in the DataServiceList
    is set via the __setitem__ method. The callbacks receive the index of the changed
    item and its new value as arguments.

    The original list that is passed during initialization is kept as a private
    attribute to prevent it from being garbage collected.

    Additional callbacks can be added after initialization using the `add_callback`
    method.

    Attributes:
        callbacks (list):
            List of callback functions to be executed on item set.
    """

    def __init__(
        self,
        *args: list[Any],
        callback: list[Callable[[int, Any], None]] | None = None,
        **kwargs: Any,
    ) -> None:
        self.callbacks: list[Callable[[int, Any], None]] = []
        if isinstance(callback, list):
            self.callbacks = callback

        for item in args[0]:
            warn_if_instance_class_does_not_inherit_from_DataService(item)

        # prevent gc to delete the passed list by keeping a reference
        self._original_list = args[0]

        super().__init__(*args, **kwargs)  # type: ignore

    def __setitem__(self, key: int, value: Any) -> None:  # type: ignore
        current_value = self.__getitem__(key)

        # parse ints into floats if current value is a float
        if isinstance(current_value, float) and isinstance(value, int):
            value = float(value)

        if isinstance(current_value, u.Quantity):
            value = u.convert_to_quantity(value, str(current_value.u))
        super().__setitem__(key, value)  # type: ignore

        for callback in self.callbacks:
            callback(key, value)

    def add_callback(self, callback: Callable[[int, Any], None]) -> None:
        """
        Add a new callback function to be executed on item set.

        Args:
            callback (Callable[[int, Any], None]): Callback function that takes two
            arguments - index of the changed item and its new value.
        """
        self.callbacks.append(callback)
