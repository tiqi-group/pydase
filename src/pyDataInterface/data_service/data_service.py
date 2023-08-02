import inspect
from collections.abc import Callable
from typing import Any

import rpyc
from loguru import logger

from pyDataInterface.utils import (
    get_class_and_instance_attributes,
    warn_if_instance_class_does_not_inherit_from_DataService,
)

from .data_service_list import DataServiceList
from .data_service_serializer import DataServiceSerializer
from .task_manager import TaskManager


class DataService(rpyc.Service, TaskManager, DataServiceSerializer):
    _list_mapping: dict[int, DataServiceList] = {}
    """
    A dictionary mapping the id of the original lists to the corresponding
    DataServiceList instances.
    This is used to ensure that all references to the same list within the DataService
    object point to the same DataServiceList, so that any modifications to that list can
    be tracked consistently. The keys of the dictionary are the ids of the original
    lists, and the values are the DataServiceList instances that wrap these lists.
    """
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
    DataService or DataServiceList instances), the _emit_notification method is invoked,
    which in turn calls all the callback functions in _notification_callbacks with the
    appropriate arguments.

    This implementation follows the observer pattern, with the DataService instance as
    the "subject" and the callback functions as the "observers".
    """

    def __init__(self) -> None:
        TaskManager.__init__(self)
        DataServiceSerializer.__init__(self, "serialized.json")
        self.__root__: "DataService" = self
        """Keep track of the root object. This helps to filter the emission of
        notifications. This overwrite the TaksManager's __root__ attribute."""

        self._callbacks: set[Callable[[str, Any], None]] = set()

        self._register_callbacks()
        self.__check_instance_classes()
        self._initialised = True

    def __setattr__(self, __name: str, __value: Any) -> None:
        current_value = getattr(self, __name, None)
        # parse ints into floats if current value is a float
        if isinstance(current_value, float) and isinstance(__value, int):
            __value = float(__value)

        super().__setattr__(__name, __value)

        if self.__dict__.get("_initialised") and not __name == "_initialised":
            for callback in self._callbacks:
                callback(__name, __value)
        elif __name.startswith(f"_{self.__class__.__name__}__"):
            logger.warning(
                f"Warning: You should not set private but rather protected attributes! "
                f"Use {__name.replace(f'_{self.__class__.__name__}__', '_')} instead "
                f"of {__name.replace(f'_{self.__class__.__name__}__', '__')}."
            )

    def _rpyc_getattr(self, name: str) -> Any:
        if name.startswith("_"):
            # disallow special and private attributes
            raise AttributeError("cannot access private/special names")
        # allow all other attributes
        return getattr(self, name)

    def _rpyc_setattr(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            # disallow special and private attributes
            raise AttributeError("cannot access private/special names")

        # check if the attribute has a setter method
        attr = getattr(self, name, None)
        if isinstance(attr, property) and attr.fset is None:
            raise AttributeError(f"{name} attribute does not have a setter method")

        # allow all other attributes
        setattr(self, name, value)

    def _register_callbacks(self) -> None:
        self._register_list_change_callbacks(self, f"{self.__class__.__name__}")
        self._register_DataService_instance_callbacks(
            self, f"{self.__class__.__name__}"
        )
        self._register_property_callbacks(self, f"{self.__class__.__name__}")
        self._register_start_stop_task_callbacks(self, f"{self.__class__.__name__}")

    def _register_list_change_callbacks(  # noqa: C901
        self, obj: "DataService", parent_path: str
    ) -> None:
        """
        This method ensures that notifications are emitted whenever a list attribute of
        a DataService instance changes. These notifications pertain solely to the list
        item changes, not to changes in attributes of objects within the list.

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
            if isinstance(attr_value, DataService):
                new_path = f"{parent_path}.{attr_name}"
                self._register_list_change_callbacks(attr_value, new_path)
            elif isinstance(attr_value, list):
                # Create callback for current attr_name
                # Default arguments solve the late binding problem by capturing the
                # value at the time the lambda is defined, not when it is called. This
                # prevents attr_name from being overwritten in the next loop iteration.
                callback = (
                    lambda index, value, attr_name=attr_name: self._emit_notification(
                        parent_path=parent_path,
                        name=f"{attr_name}[{index}]",
                        value=value,
                    )
                    if self == self.__root__
                    else None
                )

                # Check if attr_value is already a DataServiceList or in the mapping
                if isinstance(attr_value, DataServiceList):
                    attr_value.add_callback(callback)
                    continue
                if id(attr_value) in self._list_mapping:
                    notifying_list = self._list_mapping[id(attr_value)]
                    notifying_list.add_callback(callback)
                else:
                    notifying_list = DataServiceList(attr_value, callback=[callback])
                    self._list_mapping[id(attr_value)] = notifying_list

                setattr(obj, attr_name, notifying_list)

                # recursively add callbacks to list attributes of DataService instances
                for i, item in enumerate(attr_value):
                    if isinstance(item, DataService):
                        new_path = f"{parent_path}.{attr_name}[{i}]"
                        self._register_list_change_callbacks(item, new_path)

    def _register_DataService_instance_callbacks(
        self, obj: "DataService", parent_path: str
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
            lambda name, value: obj._emit_notification(
                parent_path=parent_path, name=name, value=value
            )
            if self == obj.__root__
            and not name.startswith("_")  # we are only interested in public attributes
            and not isinstance(
                getattr(type(obj), name, None), property
            )  # exlude proerty notifications -> those are handled in separate callbacks
            else None
        )

        obj._callbacks.add(callback)

        # Recursively register callbacks for all nested attributes of the object
        attrs = get_class_and_instance_attributes(obj)

        for nested_attr_name, nested_attr in attrs.items():
            if isinstance(nested_attr, DataServiceList):
                self._register_list_callbacks(
                    nested_attr, parent_path, nested_attr_name
                )
            elif isinstance(nested_attr, DataService):
                self._register_service_callbacks(
                    nested_attr, parent_path, nested_attr_name
                )

    def _register_list_callbacks(
        self, nested_attr: list[Any], parent_path: str, attr_name: str
    ) -> None:
        """Handles registration of callbacks for list attributes"""
        for i, list_item in enumerate(nested_attr):
            if isinstance(list_item, DataService):
                self._register_service_callbacks(
                    list_item, parent_path, f"{attr_name}[{i}]"
                )

    def _register_service_callbacks(
        self, nested_attr: "DataService", parent_path: str, attr_name: str
    ) -> None:
        """Handles registration of callbacks for DataService attributes"""

        # as the DataService is an attribute of self, change the root object
        # use the dictionary to not trigger callbacks on initialised objects
        nested_attr.__dict__["__root__"] = self.__root__

        new_path = f"{parent_path}.{attr_name}"
        self._register_DataService_instance_callbacks(nested_attr, new_path)

    def __register_recursive_parameter_callback(
        self,
        obj: "DataService | DataServiceList",
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
            obj_list: DataServiceList | list[DataService] = obj
        else:
            obj_list = [obj]

        # this enables notifications when a class instance was  changed (-> item is
        # changed, not reassigned)
        for item in obj_list:
            if isinstance(item, DataService):
                item._callbacks.add(callback)
                for attr_name in set(dir(item)) - set(dir(object)) - {"__root__"}:
                    attr_value = getattr(item, attr_name)
                    if isinstance(attr_value, (DataService, DataServiceList)):
                        self.__register_recursive_parameter_callback(
                            attr_value, callback
                        )

    def _register_property_callbacks(  # noqa: C901
        self,
        obj: "DataService",
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
            if isinstance(attr_value, DataService):
                self._register_property_callbacks(
                    attr_value, parent_path=f"{parent_path}.{attr_name}"
                )
            elif isinstance(attr_value, DataServiceList):
                for i, item in enumerate(attr_value):
                    if isinstance(item, DataService):
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

                    if isinstance(dependency_value, (DataServiceList, DataService)):
                        callback = (
                            lambda name, value, dependent_attr=attr_name: obj._emit_notification(
                                parent_path=parent_path,
                                name=dependent_attr,
                                value=getattr(obj, dependent_attr),
                            )
                            if self == obj.__root__
                            else None
                        )

                        self.__register_recursive_parameter_callback(
                            dependency_value,
                            callback=callback,
                        )
                    else:
                        callback = (
                            lambda name, _, dependent_attr=attr_name, dep=dependency: obj._emit_notification(  # type: ignore
                                parent_path=parent_path,
                                name=dependent_attr,
                                value=getattr(obj, dependent_attr),
                            )
                            if name == dep and self == obj.__root__
                            else None
                        )
                        # Add to _callbacks
                        obj._callbacks.add(callback)

    def __check_instance_classes(self) -> None:
        for attr_name, attr_value in get_class_and_instance_attributes(self).items():
            # every class defined by the user should inherit from DataService
            if not attr_name.startswith("_DataService__"):
                warn_if_instance_class_does_not_inherit_from_DataService(attr_value)

    def _emit_notification(self, parent_path: str, name: str, value: Any) -> None:
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

    def apply_updates(self, data: dict[str, Any]) -> None:
        """
        Applies updates to the attributes of this DataService instance.

        For each key-value pair in the provided data dictionary, this function
        checks if the attribute with the corresponding name exists in the instance,
        and if the current value of this attribute is different from the new value.
        If the attribute exists and the values are different, it updates the attribute
        in the instance with the new value.

        Args:
            data (dict): A dictionary containing the updates to be applied. The keys
                should correspond to the names of attributes in the DataService instance
                and the values should be the new values for these attributes.

        Note:
            This function assumes that all values can be directly compared with
            the != operator and assigned with the = operator. If some attributes need
            more complex update logic, this function might not work correctly for them.
        """

        # TODO: check if attribute is DataService instance -> nested updates?
        # Might not be necessary as each DataService instance change would trigger its
        # own frontend_update notification.

        for key, new_value in data.items():
            if hasattr(self, key):
                current_value = getattr(self, key)
                if current_value != new_value:
                    setattr(self, key, new_value)
            else:
                logger.error(
                    f"Attribute {key} does not exist in the DataService instance."
                )
