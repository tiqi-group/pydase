import asyncio
import inspect
import logging
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import Any, Concatenate, Generic, ParamSpec, Self, TypeVar

import pydase

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class TaskStatus(Enum):
    RUNNING = "running"
    NOT_RUNNING = "not_running"


class Task(pydase.DataService, Generic[P, R]):
    def __init__(
        self,
        func: Callable[Concatenate[Any, P], Coroutine[None, None, R | None]],
    ) -> None:
        super().__init__()
        self._func = func
        self._bound_func: Callable[P, Coroutine[None, None, R | None]] | None = None
        self._task: asyncio.Task[R] | None = None
        self._status = TaskStatus.NOT_RUNNING
        self._result: R | None = None

    @property
    def status(self) -> TaskStatus:
        return self._status

    def start(self, *args: P.args, **kwargs: P.kwargs) -> None:
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
                    self._func.__name__,
                    type(exception).__name__,
                    exception,
                )
                raise exception

            self._result = task.result()

        logger.info("Starting task")
        if inspect.iscoroutinefunction(self._bound_func):
            res: Coroutine[None, None, R] = self._bound_func(*args, **kwargs)
            self._task = asyncio.create_task(res)
            self._task.add_done_callback(task_done_callback)
            self._status = TaskStatus.RUNNING

    def stop(self) -> None:
        if self._task:
            self._task.cancel()

    def __get__(self, instance: Any, owner: Any) -> Self:
        # need to use this descriptor to bind the function to the instance of the class
        # containing the function
        if instance:

            async def bound_func(*args, **kwargs) -> R | None:
                return await self._func(instance, *args, **kwargs)

            self._bound_func = bound_func
        return self
