import asyncio
import inspect
import threading
from collections.abc import Callable
from concurrent.futures import Future
from typing import Any, cast

import rpyc
from loguru import logger

from .data_service_list import DataServiceList


class DataService(rpyc.Service):
    _full_access_path: set[str]
    """ TODO: improve this docstring
    A set of strings, each representing a unique path to access the attribute from an
    exposed class instance. Each path starts with the name of the exposed class. It's
    dynamically updated to accurately represent the current attribute structure.
    This attribute is used to emit notifications to a web server whenever the attribute
    changes, allowing for real-time tracking and updates of class instance
    modifications.

    Example:
    --------
    >>> class SubClass(DataService):
    >>>     pass

    >>> class ExposedClass(DataService):
    >>>     attr = SubClass()

    >>> service = ExposedClass()
    >>> # ... expose class

    >>> print(service.attr._full_access_path)  # {"ServiceClass.attr"}

    Have a look at tests/test_full_access_path.py to see more examples.
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

    def __init__(self) -> None:
        # dictionary to keep track of running tasks
        self.__tasks: dict[str, Future[None]] = {}
        self._autostart_tasks: dict[str, tuple[Any]]
        if "_autostart_tasks" not in self.__dict__:
            self._autostart_tasks = {}

        self._set_start_and_stop_for_async_methods()

        self._start_async_loop_in_thread()
        self._start_autostart_tasks()

        self._update_full_access_path(self, f"{self.__class__.__name__}")
        self._turn_lists_into_notify_lists()
        self._do_something_with_properties()
        self._initialised = True

    def _do_something_with_properties(self) -> None:
        for attr_name in dir(self.__class__):
            attr_value = getattr(self.__class__, attr_name)
            if isinstance(attr_value, property):  # If attribute is a property
                logger.debug(attr_value.fget.__code__.co_names)

    def _turn_lists_into_notify_lists(self) -> None:
        def create_callback(attr_name: str) -> Callable:
            """TODO: explain what this is used for...
            Create a callback with current attr_name captured in the default argument.

            Default arguments solve the late binding problem by capturing the value at
            the time the lambda is defined, not when it is called, thus preventing
            attr_name from being overwritten in another loop iteratianother
            """

            return lambda index, value, attr_name=attr_name: self._emit(
                access_path=self._full_access_path,
                name=f"{attr_name}[{index}]",
                value=value,
            )

        # Convert all list attributes (both class and instance) to DataServiceList
        for attr_name in set(dir(self)) - set(dir(object)):
            attr_value = getattr(self, attr_name)

            if isinstance(attr_value, list):
                # Create callback for current attr_name
                callback = create_callback(attr_name)

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

                setattr(self, attr_name, notifying_list)

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

    def _start_async_loop_in_thread(self) -> None:
        # create a new event loop and run it in a separate thread
        self.__loop = asyncio.new_event_loop()
        self.__thread = threading.Thread(target=self._start_loop)
        self.__thread.start()

    def _set_start_and_stop_for_async_methods(self) -> None:
        # inspect the methods of the class
        for name, method in inspect.getmembers(
            self, predicate=inspect.iscoroutinefunction
        ):

            def start_task(*args: Any, **kwargs: Any) -> None:
                async def task(*args: Any, **kwargs: Any) -> None:
                    try:
                        await getattr(self, name)(*args, **kwargs)
                    except asyncio.CancelledError:
                        print(f"Task {name} was cancelled")

                self.__tasks[name] = asyncio.run_coroutine_threadsafe(
                    task(*args, **kwargs), self.__loop
                )

            def stop_task() -> None:
                # cancel the task
                task = self.__tasks.get(name)
                if task is not None:
                    self.__loop.call_soon_threadsafe(task.cancel)

            # create start and stop methods for each coroutine
            setattr(self, f"start_{name}", start_task)
            setattr(self, f"stop_{name}", stop_task)

    def _update_full_access_path(self, obj: "DataService", parent_path: str) -> None:
        """
        Recursive helper function to update '_full_access_path' for the object and all
        its nested attributes
        """

        parent_class_name = parent_path.split(".")[0] if parent_path else None

        # Remove all access paths that don't start with the parent class name. As the
        # exposed class is instantiated last, this ensures that all access paths start
        # with the root class
        access_path: set[str] = {
            p
            for p in cast(list[str], getattr(obj, "_full_access_path", set()))
            if not parent_class_name or p.startswith(parent_class_name)
        }
        # add the new access path
        access_path.add(parent_path)
        setattr(obj, "_full_access_path", access_path)

        # Recursively update access paths for all nested attributes of the object
        for nested_attr_name in set(dir(obj)) - set(dir(object)):
            nested_attr = getattr(obj, nested_attr_name)
            if isinstance(nested_attr, list):
                for i, list_item in enumerate(nested_attr):
                    if isinstance(list_item, DataService):
                        new_path = f"{parent_path}.{nested_attr_name}[{i}]"
                        self._update_full_access_path(list_item, new_path)
            elif isinstance(nested_attr, DataService):
                new_path = f"{parent_path}.{nested_attr_name}"
                self._update_full_access_path(nested_attr, new_path)

    def _start_loop(self) -> None:
        asyncio.set_event_loop(self.__loop)
        try:
            self.__loop.run_forever()
        finally:
            # cancel all running tasks
            for task in self.__tasks.values():
                self.__loop.call_soon_threadsafe(task.cancel)
            self.__loop.call_soon_threadsafe(self.__loop.stop)
            self.__thread.join()

    def __setattr__(self, __name: str, __value: Any) -> None:
        if self.__dict__.get("_initialised"):
            access_path: set[str] = getattr(self, "_full_access_path", set())
            if access_path:
                self._emit(access_path, __name, __value)
            # TODO: add emits for properties -> can use co_names, which is a tuple
            # containing the names used by the bytecode
        super().__setattr__(__name, __value)

    def _emit(self, access_path: set[str], name: str, value: Any) -> None:
        for path in access_path:
            logger.debug(f"{path}.{name} changed to {value}!")

    def _rpyc_getattr(self, name: str) -> Any:
        if name.startswith("_"):
            # disallow special and private attributes
            raise AttributeError("cannot access private/special names")
        # allow all other attributes
        return getattr(self, name)

    def _rpyc_setattr(self, name: str, value: Any):
        if name.startswith("_"):
            # disallow special and private attributes
            raise AttributeError("cannot access private/special names")

        # check if the attribute has a setter method
        attr = getattr(self, name, None)
        if isinstance(attr, property) and attr.fset is None:
            raise AttributeError(f"{name} attribute does not have a setter method")

        # allow all other attributes
        setattr(self, name, value)

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
        base_dict = set(super().__class__.__dict__)
        # Get the dictionary of the derived class
        derived_dict = set(self.__class__.__dict__)
        # Get the difference between the two dictionaries
        derived_only_dict = derived_dict - base_dict

        instance_dict = set(self.__dict__)
        # Merge the class and instance dictionaries
        merged_dict = derived_only_dict | instance_dict

        # Iterate over attributes, properties, class attributes, and methods
        for key in merged_dict:
            if key.startswith("_"):
                continue  # Skip attributes that start with underscore

            # Get the value of the current attribute or method
            value = getattr(self, key)

            # Prepare the key by appending prefix and the key
            key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, DataService):
                result[key] = {
                    "type": type(value).__name__,
                    "value": value.serialize(prefix=key),
                    "readonly": False,
                    "id": id(value),
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
                            "id": id(item),
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
