import asyncio
import inspect
import logging
import sys
from collections.abc import Callable, Coroutine
from typing import (
    Any,
    Generic,
    TypeVar,
)

from typing_extensions import TypeIs

from pydase.task.task_status import TaskStatus

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

import pydase.data_service.data_service
from pydase.utils.helpers import current_event_loop_exists

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

R = TypeVar("R")


def is_bound_method(
    method: Callable[[], Coroutine[None, None, R | None]]
    | Callable[[Any], Coroutine[None, None, R | None]],
) -> TypeIs[Callable[[], Coroutine[None, None, R | None]]]:
    """Check if instance method is bound to an object."""
    return inspect.ismethod(method)


class Task(pydase.data_service.data_service.DataService, Generic[R]):
    """
    A class representing a task within the `pydase` framework.

    The `Task` class wraps an asynchronous function and provides methods to manage its
    lifecycle, such as `start()` and `stop()`. It is typically used to perform periodic
    or recurring jobs in a [`DataService`][pydase.DataService], like reading
    sensor data, updating databases, or executing other background tasks.

    When a function is decorated with the [`@task`][pydase.task.decorator.task]
    decorator, it is replaced by a `Task` instance that controls the execution of the
    original function.

    Args:
        func:
            The asynchronous function that this task wraps. It must be a coroutine
            without arguments.
        autostart:
            If set to True, the task will automatically start when the service is
            initialized. Defaults to False.

    Example:
        ```python
        import asyncio

        import pydase
        from pydase.task.decorator import task


        class MyService(pydase.DataService):
            @task(autostart=True)
            async def my_task(self) -> None:
                while True:
                    # Perform some periodic work
                    await asyncio.sleep(1)


        if __name__ == "__main__":
            service = MyService()
            pydase.Server(service=service).run()
        ```

        In this example, `my_task` is defined as a task using the `@task` decorator, and
        it will start automatically when the service is initialized because
        `autostart=True` is set. You can manually start or stop the task using
        `service.my_task.start()` and `service.my_task.stop()`, respectively.
    """

    def __init__(
        self,
        func: Callable[[Any], Coroutine[None, None, R | None]]
        | Callable[[], Coroutine[None, None, R | None]],
        *,
        autostart: bool = False,
    ) -> None:
        super().__init__()
        self._autostart = autostart
        self._func_name = func.__name__
        self._bound_func: Callable[[], Coroutine[None, None, R | None]] | None = None
        self._set_up = False
        if is_bound_method(func):
            self._func = func
            self._bound_func = func
        else:
            self._func = func
        self._task: asyncio.Task[R | None] | None = None
        self._status = TaskStatus.NOT_RUNNING
        self._result: R | None = None

    @property
    def autostart(self) -> bool:
        """Defines if the task should be started automatically when the
        [`Server`][pydase.Server] starts."""
        return self._autostart

    @property
    def status(self) -> TaskStatus:
        """Returns the current status of the task."""
        return self._status

    def start(self) -> None:
        """Starts the asynchronous task if it is not already running."""
        if self._task:
            return

        def task_done_callback(task: asyncio.Task[R | None]) -> None:
            """Handles tasks that have finished.

            Updates the task status, calls the defined callbacks, and logs and re-raises
            exceptions.
            """

            self._task = None
            self._status = TaskStatus.NOT_RUNNING

            exception = task.exception()
            if exception is not None:
                # Handle the exception, or you can re-raise it.
                logger.error(
                    "Task '%s' encountered an exception: %s: %s",
                    self._func_name,
                    type(exception).__name__,
                    exception,
                )
                raise exception

            self._result = task.result()

        async def run_task() -> R | None:
            if inspect.iscoroutinefunction(self._bound_func):
                logger.info("Starting task %r", self._func_name)
                self._status = TaskStatus.RUNNING
                res: Coroutine[None, None, R] = self._bound_func()
                try:
                    return await res
                except asyncio.CancelledError:
                    logger.info("Task '%s' was cancelled", self._func_name)
                    return None
            logger.warning(
                "Cannot start task %r. Function has not been bound yet", self._func_name
            )
            return None

        logger.info("Creating task %r", self._func_name)
        self._task = self._loop.create_task(run_task())
        self._task.add_done_callback(task_done_callback)

    def stop(self) -> None:
        """Stops the running asynchronous task by cancelling it."""

        if self._task:
            self._task.cancel()

    def __get__(self, instance: Any, owner: Any) -> Self:
        """Descriptor method used to correctly set up the task.

        This descriptor method is called by the class instance containing the task.
        It binds the task function to that class instance.

        Since the `__init__` function is called when a function is decorated with
        [`@task`][pydase.task.decorator.task], some setup is delayed until this
        descriptor function is called.
        """

        if instance and not self._set_up:
            if not current_event_loop_exists():
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            else:
                self._loop = asyncio.get_event_loop()
            self._bound_func = self._func.__get__(instance, owner)
            self._set_up = True
        return self
