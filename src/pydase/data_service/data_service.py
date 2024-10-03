import inspect
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any

import pydase.units as u
from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.observer_pattern.observable.observable import (
    Observable,
)
from pydase.utils.helpers import (
    get_class_and_instance_attributes,
    is_descriptor,
    is_property_attribute,
)
from pydase.utils.serialization.serializer import (
    SerializedObject,
    Serializer,
)

logger = logging.getLogger(__name__)


class DataService(AbstractDataService):
    def __init__(self) -> None:
        super().__init__()
        self.__check_instance_classes()

    def __setattr__(self, __name: str, __value: Any) -> None:
        # Check and warn for unexpected type changes in attributes
        self._warn_on_type_change(__name, __value)

        # every class defined by the user should inherit from DataService if it is
        # assigned to a public attribute
        if not __name.startswith("_") and not inspect.isfunction(__value):
            self.__warn_if_not_observable(__value)

        # Set the attribute
        super().__setattr__(__name, __value)

    def _warn_on_type_change(self, attr_name: str, new_value: Any) -> None:
        if is_property_attribute(self, attr_name):
            return

        current_value = getattr(self, attr_name, None)
        if self._is_unexpected_type_change(current_value, new_value):
            logger.warning(
                "Type of '%s' changed from '%s' to '%s'. This may have unwanted "
                "side effects! Consider setting it to '%s' directly.",
                attr_name,
                type(current_value).__name__,
                type(new_value).__name__,
                type(current_value).__name__,
            )

    def _is_unexpected_type_change(self, current_value: Any, new_value: Any) -> bool:
        return (
            isinstance(current_value, float)
            and not isinstance(new_value, float)
            or (
                isinstance(current_value, u.Quantity)
                and not isinstance(new_value, u.Quantity)
            )
        )

    def __warn_if_not_observable(self, __value: Any) -> None:
        value_class = __value if inspect.isclass(__value) else __value.__class__

        if not issubclass(
            value_class,
            (
                int
                | float
                | bool
                | str
                | list
                | dict
                | Enum
                | u.Quantity
                | Observable
                | Callable
            ),
        ) and not is_descriptor(__value):
            logger.warning(
                "Class '%s' does not inherit from DataService. This may lead to"
                " unexpected behaviour!",
                value_class.__name__,
            )

    def __check_instance_classes(self) -> None:
        for attr_name, attr_value in get_class_and_instance_attributes(self).items():
            # every class defined by the user should inherit from DataService if it is
            # assigned to a public attribute
            if (
                not attr_name.startswith("_")
                and not inspect.isfunction(attr_value)
                and not isinstance(attr_value, property)
            ):
                self.__warn_if_not_observable(attr_value)

    def serialize(self) -> SerializedObject:
        """
        Serializes the instance into a dictionary, preserving the structure of the
        instance.

        For each attribute, method, and property, the method includes its name, type,
        value, readonly status, and documentation if any in the resulting dictionary.
        Attributes and methods starting with an underscore are ignored.

        For nested DataService instances, the method serializes recursively.
        For attributes of type list, each item in the list is serialized individually.
        If an item in the list is an instance of DataService, it is serialized
        recursively.

        Returns:
            dict: The serialized instance.
        """
        return Serializer.serialize_object(self)
