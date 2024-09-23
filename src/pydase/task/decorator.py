import logging
from collections.abc import Callable, Coroutine
from typing import Any, Generic, TypeVar, overload

from pydase.data_service.data_service import DataService
from pydase.task.task import Task

logger = logging.getLogger(__name__)

R = TypeVar("R")


class PerInstanceTaskDescriptor(Generic[R]):
    """
    A descriptor class that provides a unique [`Task`][pydase.task.task.Task] object
    for each instance of a [`DataService`][pydase.data_service.data_service.DataService]
    class.

    The `PerInstanceTaskDescriptor` is used to transform an asynchronous function into a
    task that is managed independently for each instance of a `DataService` subclass.
    This allows tasks to be initialized, started, and stopped on a per-instance basis,
    providing better control over task execution within the service.

    The `PerInstanceTaskDescriptor` is not intended to be used directly. Instead, it is
    used internally by the `@task` decorator to manage task objects for each instance of
    the service class.
    """

    def __init__(
        self,
        func: Callable[[Any], Coroutine[None, None, R]]
        | Callable[[], Coroutine[None, None, R]],
        autostart: bool = False,
    ) -> None:
        self.__func = func
        self.__autostart = autostart
        self.__task_instances: dict[object, Task[R]] = {}

    def __set_name__(self, owner: type[DataService], name: str) -> None:
        """Stores the name of the task within the owning class. This method is called
        automatically when the descriptor is assigned to a class attribute.
        """

        self.__task_name = name

    @overload
    def __get__(
        self, instance: None, owner: type[DataService]
    ) -> "PerInstanceTaskDescriptor[R]":
        """Returns the descriptor itself when accessed through the class."""

    @overload
    def __get__(self, instance: DataService, owner: type[DataService]) -> Task[R]:
        """Returns the `Task` object associated with the specific `DataService`
        instance.
        If no task exists for the instance, a new `Task` object is created and stored
        in the `__task_instances` dictionary.
        """

    def __get__(
        self, instance: DataService | None, owner: type[DataService]
    ) -> "Task[R] | PerInstanceTaskDescriptor[R]":
        if instance is None:
            return self

        # Create a new Task object for this instance, using the function's name.
        if instance not in self.__task_instances:
            self.__task_instances[instance] = instance._initialise_new_objects(
                self.__task_name,
                Task(self.__func.__get__(instance, owner), autostart=self.__autostart),
            )

        return self.__task_instances[instance]


def task(
    *, autostart: bool = False
) -> Callable[
    [
        Callable[[Any], Coroutine[None, None, R]]
        | Callable[[], Coroutine[None, None, R]]
    ],
    PerInstanceTaskDescriptor[R],
]:
    """
    A decorator to define an asynchronous function as a per-instance task within a
    [`DataService`][pydase.DataService] class.

    This decorator transforms an asynchronous function into a
    [`Task`][pydase.task.task.Task] object that is unique to each instance of the
    `DataService` class. The resulting `Task` object provides methods like `start()`
    and `stop()` to control the execution of the task, and manages the task's lifecycle
    independently for each instance of the service.

    The decorator is particularly useful for defining tasks that need to run
    periodically or perform asynchronous operations, such as polling data sources,
    updating databases, or any recurring job that should be managed within the context
    of a `DataService`.
    time.

    Args:
        autostart:
            If set to True, the task will automatically start when the service is
            initialized. Defaults to False.

    Returns:
        A decorator that wraps an asynchronous function in a
        [`PerInstanceTaskDescriptor`][pydase.task.decorator.PerInstanceTaskDescriptor]
        object, which, when accessed, provides an instance-specific
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
    ) -> PerInstanceTaskDescriptor[R]:
        return PerInstanceTaskDescriptor(func, autostart=autostart)

    return decorator
