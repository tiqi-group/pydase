import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from pydase.task.task import Task

logger = logging.getLogger(__name__)

R = TypeVar("R")


def task(
    *, autostart: bool = False
) -> Callable[
    [
        Callable[[Any], Coroutine[None, None, R]]
        | Callable[[], Coroutine[None, None, R]]
    ],
    Task[R],
]:
    """
    A decorator to define a function as a task within a
    [`DataService`][pydase.DataService] class.

    This decorator transforms an asynchronous function into a
    [`Task`][pydase.task.task.Task] object. The `Task` object provides methods like
    `start()` and `stop()` to control the execution of the task.

    Tasks are typically used to perform periodic or recurring jobs, such as reading
    sensor data, updating databases, or other operations that need to be repeated over
    time.

    Args:
        autostart:
            If set to True, the task will automatically start when the service is
            initialized. Defaults to False.

    Returns:
        A decorator that converts an asynchronous function into a
          [`Task`][pydase.task.task.Task] object.

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

    def decorator(
        func: Callable[[Any], Coroutine[None, None, R]]
        | Callable[[], Coroutine[None, None, R]],
    ) -> Task[R]:
        return Task(func, autostart=autostart)

    return decorator
