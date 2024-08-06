import asyncio
import inspect
import logging
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import (
    Any,
    Generic,
    Self,
    TypeVar,
)

from typing_extensions import TypeIs

import pydase
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


class TaskStatus(Enum):
    RUNNING = "running"
    NOT_RUNNING = "not_running"


class Task(pydase.DataService, Generic[R]):
    def __init__(
        self,
        func: Callable[[Any], Coroutine[None, None, R | None]]
        | Callable[[], Coroutine[None, None, R | None]],
        *,
        autostart: bool = False,
    ) -> None:
        super().__init__()
        if not current_event_loop_exists():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        else:
            self._loop = asyncio.get_event_loop()
        self._func_name = func.__name__
        self._bound_func: Callable[[], Coroutine[None, None, R | None]] | None = None
        if is_bound_method(func):
            self._func = func
            self._bound_func = func
        else:
            self._func = func
        self._task: asyncio.Task[R] | None = None
        self._status = TaskStatus.NOT_RUNNING
        self._result: R | None = None
        if autostart:
            self.start()

    @property
    def status(self) -> TaskStatus:
        return self._status

    def start(self) -> None:
        if self._task:
            return

        def task_done_callback(task: asyncio.Task[R]) -> None:
            """Handles tasks that have finished.

            Removes a task from the tasks dictionary, calls the defined
            callbacks, and logs and re-raises exceptions."""

            # removing the finished task from the tasks i
            self._task = None

            # emit the notification that the task was stopped
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

        logger.info("Starting task %s", self._func_name)
        if inspect.iscoroutinefunction(self._bound_func):
            res: Coroutine[None, None, R] = self._bound_func()
            self._task = asyncio.create_task(res)
            self._task.add_done_callback(task_done_callback)
            self._status = TaskStatus.RUNNING

    def stop(self) -> None:
        if self._task:
            self._task.cancel()

    def __get__(self, instance: Any, owner: Any) -> Self:
        # need to use this descriptor to bind the function to the instance of the class
        # containing the function
        if instance and self._bound_func is None:
            self._bound_func = self._func.__get__(instance, owner)
        return self
