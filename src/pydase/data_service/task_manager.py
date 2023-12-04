from __future__ import annotations

import asyncio
import inspect
import logging
from functools import wraps
from typing import TYPE_CHECKING, Any, TypedDict

from pydase.data_service.abstract_data_service import AbstractDataService
from pydase.utils.helpers import get_class_and_instance_attributes

if TYPE_CHECKING:
    from collections.abc import Callable

    from .data_service import DataService

logger = logging.getLogger(__name__)


class TaskDict(TypedDict):
    task: asyncio.Task[None]
    kwargs: dict[str, Any]


class TaskManager:
    """
    The TaskManager class is a utility designed to manage asynchronous tasks. It
    provides functionality for starting, stopping, and tracking these tasks. The class
    is primarily used by the DataService class to manage its tasks.

    A task in TaskManager is any asynchronous function. To add a task, you simply need
    to define an async function within your class that extends TaskManager. For example:

    ```python
    class MyService(DataService):
        async def my_task(self):
            # Your task implementation here
            pass
    ```

    With the above definition, TaskManager automatically creates `start_my_task` and
    `stop_my_task` methods that can be used to control the task.

    TaskManager also supports auto-starting tasks. If there are tasks that should start
    running as soon as an instance of your class is created, you can define them in
    `self._autostart_tasks` in your class constructor (__init__ method). Here's how:

    ```python
    class MyService(DataService):
        def __init__(self):
            self._autostart_tasks = {
                "my_task": (*args)  # Replace with actual arguments
            }
            self.wait_time = 1
            super().__init__()

        async def my_task(self, *args):
            while True:
                # Your task implementation here
                await asyncio.sleep(self.wait_time)
    ```

    In the above example, `my_task` will start running as soon as
    `_start_autostart_tasks` is called which is done when the DataService instance is
    passed to the `pydase.Server` class.

    The responsibilities of the TaskManager class are:

    - Track all running tasks: Keeps track of all the tasks that are currently running.
    This allows for monitoring of task statuses and for making sure tasks do not
    overlap.
    - Provide the ability to start and stop tasks: Automatically creates methods to
    start and stop each task.
    - Emit notifications when the status of a task changes: Has a built-in mechanism for
    emitting notifications when a task starts or stops. This is used to update the user
    interfaces, but can also be used to write logs, etc.
    """

    def __init__(self, service: DataService) -> None:
        self.service = service
        self._loop = asyncio.get_event_loop()

        self.tasks: dict[str, TaskDict] = {}
        """A dictionary to keep track of running tasks. The keys are the names of the
        tasks and the values are TaskDict instances which include the task itself and
        its kwargs.
        """

        self._set_start_and_stop_for_async_methods()

    def _set_start_and_stop_for_async_methods(self) -> None:
        # inspect the methods of the class
        for name, method in inspect.getmembers(
            self.service, predicate=inspect.iscoroutinefunction
        ):
            # create start and stop methods for each coroutine
            setattr(self.service, f"start_{name}", self._make_start_task(name, method))
            setattr(self.service, f"stop_{name}", self._make_stop_task(name))

    def _initiate_task_startup(self) -> None:
        if self.service._autostart_tasks is not None:
            for service_name, args in self.service._autostart_tasks.items():
                start_method = getattr(self.service, f"start_{service_name}", None)
                if start_method is not None and callable(start_method):
                    start_method(*args)
                else:
                    logger.warning(
                        "No start method found for service '%s'", service_name
                    )

    def start_autostart_tasks(self) -> None:
        self._initiate_task_startup()
        attrs = get_class_and_instance_attributes(self.service)

        for attr_value in attrs.values():
            if isinstance(attr_value, AbstractDataService):
                attr_value._task_manager.start_autostart_tasks()
            elif isinstance(attr_value, list):
                for item in attr_value:
                    if isinstance(item, AbstractDataService):
                        item._task_manager.start_autostart_tasks()

    def _make_stop_task(self, name: str) -> Callable[..., Any]:
        """
        Factory function to create a 'stop_task' function for a running task.

        The generated function cancels the associated asyncio task using 'name' for
        identification, ensuring proper cleanup. Avoids closure and late binding issues.

        Args:
            name (str): The name of the coroutine task, used for its identification.
        """

        def stop_task() -> None:
            # cancel the task
            task = self.tasks.get(name, None)
            if task is not None:
                self._loop.call_soon_threadsafe(task["task"].cancel)

        return stop_task

    def _make_start_task(
        self, name: str, method: Callable[..., Any]
    ) -> Callable[..., Any]:
        """
        Factory function to create a 'start_task' function for a coroutine.

        The generated function starts the coroutine as an asyncio task, handling
        registration and monitoring.
        It uses 'name' and 'method' to avoid the closure and late binding issue.

        Args:
            name (str): The name of the coroutine, used for task management.
            method (callable): The coroutine to be turned into an asyncio task.
        """

        @wraps(method)
        def start_task(*args: Any, **kwargs: Any) -> None:
            def task_done_callback(task: asyncio.Task[None], name: str) -> None:
                """Handles tasks that have finished.

                Removes a task from the tasks dictionary, calls the defined
                callbacks, and logs and re-raises exceptions."""

                # removing the finished task from the tasks i
                self.tasks.pop(name, None)

                # emit the notification that the task was stopped
                self.service._notify_changed(name, None)

                exception = task.exception()
                if exception is not None:
                    # Handle the exception, or you can re-raise it.
                    logger.error(
                        "Task '%s' encountered an exception: %s: %s",
                        name,
                        type(exception).__name__,
                        exception,
                    )
                    raise exception

            async def task(*args: Any, **kwargs: Any) -> None:
                try:
                    await method(*args, **kwargs)
                except asyncio.CancelledError:
                    logger.info("Task '%s' was cancelled", name)

            if not self.tasks.get(name):
                # Get the signature of the coroutine method to start
                sig = inspect.signature(method)

                # Create a list of the parameter names from the method signature.
                parameter_names = list(sig.parameters.keys())

                # Extend the list of positional arguments with None values to match
                # the length of the parameter names list. This is done to ensure
                # that zip can pair each parameter name with a corresponding value.
                args_padded = list(args) + [None] * (len(parameter_names) - len(args))

                # Create a dictionary of keyword arguments by pairing the parameter
                # names with the values in 'args_padded'. Then merge this dictionary
                # with the 'kwargs' dictionary. If a parameter is specified in both
                # 'args_padded' and 'kwargs', the value from 'kwargs' is used.
                kwargs_updated = {
                    **dict(zip(parameter_names, args_padded, strict=True)),
                    **kwargs,
                }

                # creating the task and adding the task_done_callback which checks
                # if an exception has occured during the task execution
                task_object = self._loop.create_task(task(*args, **kwargs))
                task_object.add_done_callback(
                    lambda task: task_done_callback(task, name)
                )

                # Store the task and its arguments in the '__tasks' dictionary. The
                # key is the name of the method, and the value is a dictionary
                # containing the task object and the updated keyword arguments.
                self.tasks[name] = {
                    "task": task_object,
                    "kwargs": kwargs_updated,
                }

                # emit the notification that the task was started
                self.service._notify_changed(name, kwargs_updated)
            else:
                logger.error("Task '%s' is already running!", name)

        return start_task
