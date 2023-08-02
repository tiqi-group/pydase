from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypedDict

from pyDataInterface.data_service.data_service_list import DataServiceList


class AbstractDataService(ABC):
    __root__: AbstractDataService
    _task_manager: AbstractTaskManager
    _callback_manager: AbstractCallbackManager
    """
    This is a CallbackManager. Cannot type this here as this would lead to a recursive
    loop.
    """
    _autostart_tasks: dict[str, tuple[Any]]
    # _task_status_change_callbacks: list[Callable[[str, dict[str, Any] | None], None]]
    # """A list of callback functions to be invoked when the status of a task (start or
    # stop) changes."""


class TaskDict(TypedDict):
    task: asyncio.Task[None]
    kwargs: dict[str, Any]


class AbstractTaskManager(ABC):
    _task_status_change_callbacks: list[Callable[[str, dict[str, Any] | None], Any]]
    """A list of callback functions to be invoked when the status of a task (start or
    stop) changes."""
    _tasks: dict[str, TaskDict]
    """A dictionary to keep track of running tasks. The keys are the names of the
    tasks and the values are TaskDict instances which include the task itself and
    its kwargs.
    """

    @abstractmethod
    def _set_start_and_stop_for_async_methods(self) -> None:
        ...

    @abstractmethod
    def start_autostart_tasks(self) -> None:
        ...


class AbstractCallbackManager(ABC):
    service: AbstractDataService
    callbacks: set[Callable[[str, Any], None]]
    _list_mapping: dict[int, DataServiceList]
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
    DataService or DataServiceList instances), the emit_notification method is invoked,
    which in turn calls all the callback functions in _notification_callbacks with the
    appropriate arguments.

    This implementation follows the observer pattern, with the DataService instance as
    the "subject" and the callback functions as the "observers".
    """
