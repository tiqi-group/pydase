import asyncio
import inspect
from collections.abc import Callable
from itertools import chain
from typing import Any

import rpyc
from loguru import logger

from pyDataInterface.utils import (
    warn_if_instance_class_does_not_inherit_from_DataService,
)

from .data_service_list import DataServiceList


class DataService(rpyc.Service):
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

    def __init__(self) -> None:
        # Keep track of the root object. This helps to filter the emission of
        # notifications
        self.__root__: "DataService" = self
        self.__loop = asyncio.get_event_loop()

        # dictionary to keep track of running tasks
        self.__tasks: dict[str, asyncio.Task[None]] = {}
        self._autostart_tasks: dict[str, tuple[Any]]
        if "_autostart_tasks" not in self.__dict__:
            self._autostart_tasks = {}

        self._callbacks: set[Callable[[str, Any], None]] = set()
        self._set_start_and_stop_for_async_methods()

        self._register_callbacks()
        self.__check_instance_classes()
        self._initialised = True

    def __setattr__(self, __name: str, __value: Any) -> None:
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

    def _start_autostart_tasks(self) -> None:
        if self._autostart_tasks is not None:
            for service_name, args in self._autostart_tasks.items():
                start_method = getattr(self, f"start_{service_name}", None)
                if start_method is not None and callable(start_method):
                    start_method(*args)
                else:
                    logger.warning(
                        f"No start method found for service '{service_name}'"
                    )

    def _set_start_and_stop_for_async_methods(self) -> None:  # noqa: C901
        # inspect the methods of the class
        for name, method in inspect.getmembers(
            self, predicate=inspect.iscoroutinefunction
        ):

            def start_task(*args: Any, **kwargs: Any) -> None:
                async def task(*args: Any, **kwargs: Any) -> None:
                    try:
                        await method(*args, **kwargs)
                    except asyncio.CancelledError:
                        print(f"Task {name} was cancelled")

                if not self.__tasks.get(name):
                    self.__tasks[name] = self.__loop.create_task(task(*args, **kwargs))
                else:
                    logger.error(f"Task `{name}` is already running!")

            def stop_task() -> None:
                # cancel the task
                task = self.__tasks.pop(name)
                if task is not None:
                    self.__loop.call_soon_threadsafe(task.cancel)

            # create start and stop methods for each coroutine
            setattr(self, f"start_{name}", start_task)
            setattr(self, f"stop_{name}", stop_task)

    def _register_callbacks(self) -> None:
        self._register_list_change_callbacks(self, f"{self.__class__.__name__}")
        self._register_DataService_instance_callbacks(
            self, f"{self.__class__.__name__}"
        )
        self._register_property_callbacks(self, f"{self.__class__.__name__}")

    def _register_list_change_callbacks(
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
        attrs = obj.__get_class_and_instance_attributes()

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
        attrs = obj.__get_class_and_instance_attributes()

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

    def _register_property_callbacks(
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

        attrs = obj.__get_class_and_instance_attributes()

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
                    #  ('class_attr', 'voltage', 'current')
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
                            lambda name, value, dependent_attr=attr_name, dep=dependency: obj._emit_notification(
                                parent_path=parent_path,
                                name=dependent_attr,
                                value=getattr(obj, dependent_attr),
                            )
                            if name == dep and self == obj.__root__
                            else None
                        )
                        # Add to _callbacks
                        obj._callbacks.add(callback)

    def __get_class_and_instance_attributes(self) -> dict[str, Any]:
        """Dictionary containing all attributes (both instance and class level) of a
        given object.

        If an attribute exists at both the instance and class level,the value from the
        instance attribute takes precedence.
        The __root__ object is removed as this will lead to endless recursion in the for
        loops.
        """

        attrs = dict(chain(type(self).__dict__.items(), self.__dict__.items()))
        attrs.pop("__root__")
        return attrs

    def __check_instance_classes(self) -> None:
        for attr_name, attr_value in self.__get_class_and_instance_attributes().items():
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

    def serialize(self, prefix: str = "") -> dict[str, dict[str, Any]]:
        """
        Serializes the instance into a dictionary, preserving the structure of the
        instance.

        For each attribute, method, and property, the method includes its name, type,
        value, readonly status, and documentation if any in the resulting dictionary.
        Attributes and methods starting with an underscore are ignored.

        For attributes, methods, and properties unique to the class (not inherited from
        the base class), the method uses the format "<prefix>.<key>" for keys in the
        dictionary. If no prefix is provided, the key format is simply "<key>".

        For nested DataService instances, the method serializes recursively and appends
        the key of the nested instance to the prefix in the format "<prefix>.<key>".

        For attributes of type list, each item in the list is serialized individually.
        If an item in the list is an instance of DataService, it is serialized
        recursively with its key in the format "<prefix>.<key>.<item_id>", where
        "item_id" is the id of the item itself.

        Args:
            prefix (str, optional): The prefix for each key in the serialized
            dictionary. This is mainly used when this method is called recursively to
            maintain the structure of nested instances.

        Returns:
            dict: The serialized instance.
        """
        result: dict[str, dict[str, Any]] = {}

        # Get the dictionary of the base class
        base_set = set(type(super()).__dict__)
        # Get the dictionary of the derived class
        derived_set = set(type(self).__dict__)
        # Get the difference between the two dictionaries
        derived_only_set = derived_set - base_set

        instance_dict = set(self.__dict__)
        # Merge the class and instance dictionaries
        merged_set = derived_only_set | instance_dict

        # Iterate over attributes, properties, class attributes, and methods
        for key in merged_set:
            if key.startswith("_"):
                continue  # Skip attributes that start with underscore

            # Get the value of the current attribute or method
            value = getattr(self, key)

            # Prepare the key by appending prefix and the key
            key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, DataService):
                result[key] = {
                    "type": type(value).__name__
                    if type(value).__name__ in ("NumberSlider")
                    else "DataService",
                    "value": value.serialize(),
                    "readonly": False,
                    "doc": inspect.getdoc(value),
                }
            elif isinstance(value, list):
                result[key] = {
                    "type": "list",
                    "value": [
                        {
                            "type": type(item).__name__,
                            "value": item.serialize(prefix=key)
                            if isinstance(item, DataService)
                            else item,
                            "readonly": False,
                        }
                        for item in value
                    ],
                    "readonly": False,
                }
            elif inspect.isfunction(value) or inspect.ismethod(value):
                sig = inspect.signature(value)
                parameters = {
                    k: v.annotation.__name__
                    if v.annotation is not inspect._empty
                    else None
                    for k, v in sig.parameters.items()
                }
                result[key] = {
                    "type": "method",
                    "async": asyncio.iscoroutinefunction(value),
                    "parameters": parameters,
                    "readonly": False,
                    "doc": inspect.getdoc(value),
                }
            elif isinstance(getattr(self.__class__, key, None), property):
                prop: property = getattr(self.__class__, key)
                result[key] = {
                    "type": type(value).__name__,
                    "value": value,
                    "readonly": prop.fset is None,
                    "doc": inspect.getdoc(prop),
                }
            else:
                result[key] = {
                    "type": type(value).__name__,
                    "value": value,
                    "readonly": False,
                }

        return result

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
