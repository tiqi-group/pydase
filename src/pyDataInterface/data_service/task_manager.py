import asyncio
import inspect
from abc import abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import TypedDict

from loguru import logger
from tiqi_rpc import Any

from pyDataInterface.utils import get_class_and_instance_attributes


class TaskDict(TypedDict):
    task: asyncio.Task[None]
    kwargs: dict[str, Any]


class TaskManager:
    """
    The TaskManager class is a utility class designed to manage asynchronous tasks. It
    provides functionality for starting and stopping these tasks. The class is primarily
    used by the DataService class to manage its tasks.

    The TaskManager class has the following responsibilities:

    - Track all running tasks.
    - Provide the ability to start and stop tasks.
    - Emit notifications when the status of a task changes.

    The tasks are asynchronous functions which can be started or stopped with the
    generated functions in this class.
    """

    def __init__(self) -> None:
        self.__root__: "TaskManager" = self
        """Keep track of the root object. This helps to filter the emission of
        notifications."""

        self._loop = asyncio.get_event_loop()

        self._tasks: dict[str, TaskDict] = {}
        """A dictionary to keep track of running tasks. The keys are the names of the
        tasks and the values are TaskDict instances which include the task itself and
        its kwargs.
        """

        self._task_status_change_callbacks: list[
            Callable[[str, dict[str, Any] | None], Any]
        ] = []
        """A list of callback functions to be invoked when the status of a task (start
        or stop) changes."""

        self._set_start_and_stop_for_async_methods()

    def _register_start_stop_task_callbacks(
        self, obj: "TaskManager", parent_path: str
    ) -> None:
        """
        This function registers callbacks for start and stop methods of async functions.
        These callbacks are stored in the '_task_status_change_callbacks' attribute and
        are called when the status of a task changes.

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
        callback: Callable[[str, dict[str, Any] | None], None] = (
            lambda name, status: obj._emit_notification(
                parent_path=parent_path, name=name, value=status
            )
            if self == obj.__root__
            and not name.startswith("_")  # we are only interested in public attributes
            else None
        )

        obj._task_status_change_callbacks.append(callback)

        # Recursively register callbacks for all nested attributes of the object
        attrs: dict[str, Any] = get_class_and_instance_attributes(obj)

        for nested_attr_name, nested_attr in attrs.items():
            if isinstance(nested_attr, TaskManager):
                self._register_start_stop_task_callbacks(
                    nested_attr, parent_path=f"{parent_path}.{nested_attr_name}"
                )

    def _set_start_and_stop_for_async_methods(self) -> None:  # noqa: C901
        # inspect the methods of the class
        for name, method in inspect.getmembers(
            self, predicate=inspect.iscoroutinefunction
        ):

            @wraps(method)
            def start_task(*args: Any, **kwargs: Any) -> None:
                async def task(*args: Any, **kwargs: Any) -> None:
                    try:
                        await method(*args, **kwargs)
                    except asyncio.CancelledError:
                        print(f"Task {name} was cancelled")

                if not self._tasks.get(name):
                    # Get the signature of the coroutine method to start
                    sig = inspect.signature(method)

                    # Create a list of the parameter names from the method signature.
                    parameter_names = list(sig.parameters.keys())

                    # Extend the list of positional arguments with None values to match
                    # the length of the parameter names list. This is done to ensure
                    # that zip can pair each parameter name with a corresponding value.
                    args_padded = list(args) + [None] * (
                        len(parameter_names) - len(args)
                    )

                    # Create a dictionary of keyword arguments by pairing the parameter
                    # names with the values in 'args_padded'. Then merge this dictionary
                    # with the 'kwargs' dictionary. If a parameter is specified in both
                    # 'args_padded' and 'kwargs', the value from 'kwargs' is used.
                    kwargs_updated = {
                        **dict(zip(parameter_names, args_padded)),
                        **kwargs,
                    }

                    # Store the task and its arguments in the '__tasks' dictionary. The
                    # key is the name of the method, and the value is a dictionary
                    # containing the task object and the updated keyword arguments.
                    self._tasks[name] = {
                        "task": self._loop.create_task(task(*args, **kwargs)),
                        "kwargs": kwargs_updated,
                    }

                    # emit the notification that the task was started
                    for callback in self._task_status_change_callbacks:
                        callback(name, kwargs_updated)
                else:
                    logger.error(f"Task `{name}` is already running!")

            def stop_task() -> None:
                # cancel the task
                task = self._tasks.pop(name)
                if task is not None:
                    self._loop.call_soon_threadsafe(task["task"].cancel)

                    # emit the notification that the task was stopped
                    for callback in self._task_status_change_callbacks:
                        callback(name, None)

            # create start and stop methods for each coroutine
            setattr(self, f"start_{name}", start_task)
            setattr(self, f"stop_{name}", stop_task)

    @abstractmethod
    def _emit_notification(self, parent_path: str, name: str, value: Any) -> None:
        raise NotImplementedError
