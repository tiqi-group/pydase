from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.utils.helpers import get_class_and_instance_attributes

from .data_service_list import DataServiceList

if TYPE_CHECKING:
    from .data_service import DataService

logger = logging.getLogger(__name__)


class CallbackManager:
    _notification_callbacks: list[Callable[[str, str, Any], Any]] = []
    """
    A list of callback functions that are executed when a change occurs in the
    DataService instance. These functions are intended to handle or respond to these
    changes in some way, such as emitting a socket.io message to the frontend.

    Each function in this list should be a callable that accepts three parameters:

    - parent_path (str): The path to the parent of the attribute that was changed.
    - name (str): The name of the attribute that was changed.
    - value (Any): The new value of the attribute.

    A callback function can be added to this list using the add_notification_callback
    method. Whenever a change in the DataService instance occurs (or in its nested
    DataService or DataServiceList instances), the emit_notification method is invoked,
    which in turn calls all the callback functions in _notification_callbacks with the
    appropriate arguments.

    This implementation follows the observer pattern, with the DataService instance as
    the "subject" and the callback functions as the "observers".
    """
    _list_mapping: dict[int, DataServiceList] = {}
    """
    A dictionary mapping the id of the original lists to the corresponding
    DataServiceList instances.
    This is used to ensure that all references to the same list within the DataService
    object point to the same DataServiceList, so that any modifications to that list can
    be tracked consistently. The keys of the dictionary are the ids of the original
    lists, and the values are the DataServiceList instances that wrap these lists.
    """

    def __init__(self, service: DataService) -> None:
        self.callbacks: set[Callable[[str, Any], None]] = set()
        self.service = service

    def _register_list_change_callbacks(  # noqa: C901
        self, obj: "AbstractDataService", parent_path: str
    ) -> None:
        """
        This method ensures that notifications are emitted whenever a public list
        attribute of a DataService instance changes. These notifications pertain solely
        to the list item changes, not to changes in attributes of objects within the
        list.

        The method works by converting all list attributes (both at the class and
        instance levels) into DataServiceList objects. Each DataServiceList is then
        assigned a callback that is triggered whenever an item in the list is updated.
        The callback emits a notification, but only if the DataService instance was the
        root instance when the callback was registered.

        This method operates recursively, processing the input object and all nested
        attributes that are instances of DataService. While navigating the structure,
        it constructs a path for each attribute that traces back to the root. This path
        is included in any emitted notifications to facilitate identification of the
        source of a change.

        Parameters:
        -----------
        obj: DataService
            The target object to be processed. All list attributes (and those of its
            nested DataService attributes) will be converted into DataServiceList
            objects.
        parent_path: str
            The access path for the parent object. Used to construct the full access
            path for the notifications.
        """

        # Convert all list attributes (both class and instance) to DataServiceList
        attrs = get_class_and_instance_attributes(obj)

        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, AbstractDataService):
                new_path = f"{parent_path}.{attr_name}"
                self._register_list_change_callbacks(attr_value, new_path)
            elif isinstance(attr_value, list):
                # Create callback for current attr_name
                # Default arguments solve the late binding problem by capturing the
                # value at the time the lambda is defined, not when it is called. This
                # prevents attr_name from being overwritten in the next loop iteration.
                callback = (
                    lambda index, value, attr_name=attr_name: self.service._callback_manager.emit_notification(
                        parent_path=parent_path,
                        name=f"{attr_name}[{index}]",
                        value=value,
                    )
                    if self.service == self.service.__root__
                    # Skip private and protected lists
                    and not cast(str, attr_name).startswith("_")
                    else None
                )

                # Check if attr_value is already a DataServiceList or in the mapping
                if isinstance(attr_value, DataServiceList):
                    attr_value.add_callback(callback)
                    continue
                if id(attr_value) in self._list_mapping:
                    # If the list `attr_value` was already referenced somewhere else
                    notifying_list = self._list_mapping[id(attr_value)]
                    notifying_list.add_callback(callback)
                else:
                    # convert the builtin list into a DataServiceList and add the
                    # callback
                    notifying_list = DataServiceList(attr_value, callback=[callback])
                    self._list_mapping[id(attr_value)] = notifying_list

                setattr(obj, attr_name, notifying_list)

                # recursively add callbacks to list attributes of DataService instances
                for i, item in enumerate(attr_value):
                    if isinstance(item, AbstractDataService):
                        new_path = f"{parent_path}.{attr_name}[{i}]"
                        self._register_list_change_callbacks(item, new_path)

    def _register_DataService_instance_callbacks(
        self, obj: "AbstractDataService", parent_path: str
    ) -> None:
        """
        This function is a key part of the observer pattern implemented by the
        DataService class.
        Its purpose is to allow the system to automatically send out notifications
        whenever an attribute of a DataService instance is updated, which is especially
        useful when the DataService instance is part of a nested structure.

        It works by recursively registering callbacks for a given DataService instance
        and all of its nested attributes. Each callback is responsible for emitting a
        notification when the attribute it is attached to is modified.

        This function ensures that only the root DataService instance (the one directly
        exposed to the user or another system via rpyc) emits notifications.

        Each notification contains a 'parent_path' that traces the attribute's location
        within the nested DataService structure, starting from the root. This makes it
        easier for observers to determine exactly where a change has occurred.

        Parameters:
        -----------
        obj: DataService
            The target object on which callbacks are to be registered.
        parent_path: str
            The access path for the parent object. This is used to construct the full
            access path for the notifications.
        """

        # Create and register a callback for the object
        # only emit the notification when the call was registered by the root object
        callback: Callable[[str, Any], None] = (
            lambda name, value: obj._callback_manager.emit_notification(
                parent_path=parent_path, name=name, value=value
            )
            if self.service == obj.__root__
            and not name.startswith("_")  # we are only interested in public attributes
            and not isinstance(
                getattr(type(obj), name, None), property
            )  # exlude proerty notifications -> those are handled in separate callbacks
            else None
        )

        obj._callback_manager.callbacks.add(callback)

        # Recursively register callbacks for all nested attributes of the object
        attrs = get_class_and_instance_attributes(obj)

        for nested_attr_name, nested_attr in attrs.items():
            if isinstance(nested_attr, DataServiceList):
                self._register_list_callbacks(
                    nested_attr, parent_path, nested_attr_name
                )
            elif isinstance(nested_attr, AbstractDataService):
                self._register_service_callbacks(
                    nested_attr, parent_path, nested_attr_name
                )

    def _register_list_callbacks(
        self, nested_attr: list[Any], parent_path: str, attr_name: str
    ) -> None:
        """Handles registration of callbacks for list attributes"""
        for i, list_item in enumerate(nested_attr):
            if isinstance(list_item, AbstractDataService):
                self._register_service_callbacks(
                    list_item, parent_path, f"{attr_name}[{i}]"
                )

    def _register_service_callbacks(
        self, nested_attr: "AbstractDataService", parent_path: str, attr_name: str
    ) -> None:
        """Handles registration of callbacks for DataService attributes"""

        # as the DataService is an attribute of self, change the root object
        # use the dictionary to not trigger callbacks on initialised objects
        nested_attr.__dict__["__root__"] = self.service.__root__

        new_path = f"{parent_path}.{attr_name}"
        self._register_DataService_instance_callbacks(nested_attr, new_path)

    def __register_recursive_parameter_callback(
        self,
        obj: "AbstractDataService | DataServiceList",
        callback: Callable[[str | int, Any], None],
    ) -> None:
        """
        Register callback to a DataService or DataServiceList instance and its nested
        instances.

        For a DataService, this method traverses its attributes and recursively adds the
        callback for nested DataService or DataServiceList instances. For a
        DataServiceList,
        the callback is also triggered when an item gets reassigned.
        """

        if isinstance(obj, DataServiceList):
            # emits callback when item in list gets reassigned
            obj.add_callback(callback=callback)
            obj_list: DataServiceList | list[AbstractDataService] = obj
        else:
            obj_list = [obj]

        # this enables notifications when a class instance was  changed (-> item is
        # changed, not reassigned)
        for item in obj_list:
            if isinstance(item, AbstractDataService):
                item._callback_manager.callbacks.add(callback)
                for attr_name in set(dir(item)) - set(dir(object)) - {"__root__"}:
                    attr_value = getattr(item, attr_name)
                    if isinstance(attr_value, (AbstractDataService, DataServiceList)):
                        self.__register_recursive_parameter_callback(
                            attr_value, callback
                        )

    def _register_property_callbacks(  # noqa: C901
        self,
        obj: "AbstractDataService",
        parent_path: str,
    ) -> None:
        """
        Register callbacks to notify when properties or their dependencies change.

        This method cycles through all attributes (both class and instance level) of the
        input `obj`. For each attribute that is a property, it identifies dependencies
        used in the getter method and creates a callback for each one.

        The method is recursive for attributes that are of type DataService or
        DataServiceList. It attaches the callback directly to DataServiceList items or
        propagates it through nested DataService instances.
        """

        attrs = get_class_and_instance_attributes(obj)

        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, AbstractDataService):
                self._register_property_callbacks(
                    attr_value, parent_path=f"{parent_path}.{attr_name}"
                )
            elif isinstance(attr_value, DataServiceList):
                for i, item in enumerate(attr_value):
                    if isinstance(item, AbstractDataService):
                        self._register_property_callbacks(
                            item, parent_path=f"{parent_path}.{attr_name}[{i}]"
                        )
            if isinstance(attr_value, property):
                dependencies = attr_value.fget.__code__.co_names  # type: ignore
                source_code_string = inspect.getsource(attr_value.fget)  # type: ignore

                for dependency in dependencies:
                    # check if the dependencies are attributes of obj
                    # This doesn't have to be the case like, for example, here:
                    # >>> @property
                    # >>> def power(self) -> float:
                    # >>>     return self.class_attr.voltage * self.current
                    #
                    # The dependencies for this property are:
                    # > ('class_attr', 'voltage', 'current')
                    if f"self.{dependency}" not in source_code_string:
                        continue

                    # use `obj` instead of `type(obj)` to get DataServiceList
                    # instead of list
                    dependency_value = getattr(obj, dependency)

                    if isinstance(
                        dependency_value, (DataServiceList, AbstractDataService)
                    ):
                        callback = (
                            lambda name, value, dependent_attr=attr_name: obj._callback_manager.emit_notification(
                                parent_path=parent_path,
                                name=dependent_attr,
                                value=getattr(obj, dependent_attr),
                            )
                            if self.service == obj.__root__
                            else None
                        )

                        self.__register_recursive_parameter_callback(
                            dependency_value,
                            callback=callback,
                        )
                    else:
                        callback = (
                            lambda name, _, dep_attr=attr_name, dep=dependency: obj._callback_manager.emit_notification(  # type: ignore
                                parent_path=parent_path,
                                name=dep_attr,
                                value=getattr(obj, dep_attr),
                            )
                            if name == dep and self.service == obj.__root__
                            else None
                        )
                        # Add to callbacks
                        obj._callback_manager.callbacks.add(callback)

    def _register_start_stop_task_callbacks(
        self, obj: "AbstractDataService", parent_path: str
    ) -> None:
        """
        This function registers callbacks for start and stop methods of async functions.
        These callbacks are stored in the '_task_status_change_callbacks' attribute and
        are called when the status of a task changes.

        Parameters:
        -----------
        obj: AbstractDataService
            The target object on which callbacks are to be registered.
        parent_path: str
            The access path for the parent object. This is used to construct the full
            access path for the notifications.
        """

        # Create and register a callback for the object
        # only emit the notification when the call was registered by the root object
        callback: Callable[[str, dict[str, Any] | None], None] = (
            lambda name, status: obj._callback_manager.emit_notification(
                parent_path=parent_path, name=name, value=status
            )
            if self.service == obj.__root__
            and not name.startswith("_")  # we are only interested in public attributes
            else None
        )

        obj._task_manager.task_status_change_callbacks.append(callback)

        # Recursively register callbacks for all nested attributes of the object
        attrs: dict[str, Any] = get_class_and_instance_attributes(obj)

        for nested_attr_name, nested_attr in attrs.items():
            if isinstance(nested_attr, DataServiceList):
                for i, item in enumerate(nested_attr):
                    if isinstance(item, AbstractDataService):
                        self._register_start_stop_task_callbacks(
                            item, parent_path=f"{parent_path}.{nested_attr_name}[{i}]"
                        )
            if isinstance(nested_attr, AbstractDataService):
                self._register_start_stop_task_callbacks(
                    nested_attr, parent_path=f"{parent_path}.{nested_attr_name}"
                )

    def register_callbacks(self) -> None:
        self._register_list_change_callbacks(
            self.service, f"{self.service.__class__.__name__}"
        )
        self._register_DataService_instance_callbacks(
            self.service, f"{self.service.__class__.__name__}"
        )
        self._register_property_callbacks(
            self.service, f"{self.service.__class__.__name__}"
        )
        self._register_start_stop_task_callbacks(
            self.service, f"{self.service.__class__.__name__}"
        )

    def emit_notification(self, parent_path: str, name: str, value: Any) -> None:
        logger.debug(f"{parent_path}.{name} changed to {value}!")

        for callback in self._notification_callbacks:
            try:
                callback(parent_path, name, value)
            except Exception as e:
                logger.error(e)

    def add_notification_callback(
        self, callback: Callable[[str, str, Any], None]
    ) -> None:
        """
        Adds a new notification callback function to the list of callbacks.

        This function is intended to be used for registering a function that will be
        called whenever a the value of an attribute changes.

        Args:
            callback (Callable[[str, str, Any], None]): The callback function to
            register.
                It should accept three parameters:
                - parent_path (str): The parent path of the parameter.
                - name (str): The name of the changed parameter.
                - value (Any): The value of the parameter.
        """
        self._notification_callbacks.append(callback)
