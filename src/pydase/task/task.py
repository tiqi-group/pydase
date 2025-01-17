import asyncio
import inspect
import logging
import os
import signal
from collections.abc import Callable, Coroutine
from datetime import datetime
from time import time
from typing import (
    Generic,
    TypeVar,
)

import pydase.data_service.data_service
from pydase.task.task_status import TaskStatus
from pydase.utils.helpers import current_event_loop_exists

logger = logging.getLogger(__name__)

R = TypeVar("R")


class Task(pydase.data_service.data_service.DataService, Generic[R]):
    """A class representing a task within the `pydase` framework.

    The `Task` class wraps an asynchronous function and provides methods to manage its
    lifecycle, such as `start()` and `stop()`. It is typically used to perform periodic
    or recurring jobs in a [`DataService`][pydase.DataService], like reading
    sensor data, updating databases, or executing other background tasks.

    When a function is decorated with the [`@task`][pydase.task.decorator.task]
    decorator, it is replaced by a `Task` instance that controls the execution of the
    original function.

    The keyword arguments that can be passed to this class are inspired by systemd unit
    services.

    Args:
        func:
            The asynchronous function that this task wraps. It must be a coroutine
            without arguments.
        autostart:
            If set to True, the task will automatically start when the service is
            initialized. Defaults to False.
        restart_on_failure:
            Configures whether the task shall be restarted when it exits with an
            exception other than [`asyncio.CancelledError`][asyncio.CancelledError].
        restart_sec:
            Configures the time to sleep before restarting a task. Defaults to 1.0.
        start_limit_interval_sec:
            Configures start rate limiting. Tasks which are started more than
            `start_limit_burst` times within an `start_limit_interval_sec` time span are
            not permitted to start any more. Defaults to None (disabled rate limiting).
        start_limit_burst:
            Configures unit start rate limiting. Tasks which are started more than
            `start_limit_burst` times within an `start_limit_interval_sec` time span are
            not permitted to start any more. Defaults to 3.
        timeout_start_sec:
            Configures the time to wait for start-up. Defaults to 0.0.
        exit_on_failure:
            If True, exit the service if the task fails and restart_on_failure is False
            or burst limits are exceeded.

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

    def __init__(  # noqa: PLR0913
        self,
        func: Callable[[], Coroutine[None, None, R | None]],
        *,
        autostart: bool,
        restart_on_failure: bool,
        restart_sec: float,
        start_limit_interval_sec: float | None,
        start_limit_burst: int,
        timeout_start_sec: float,
        exit_on_failure: bool,
    ) -> None:
        super().__init__()
        self._autostart = autostart
        self._restart_on_failure = restart_on_failure
        self._restart_sec = restart_sec
        self._start_limit_interval_sec = start_limit_interval_sec
        self._start_limit_burst = start_limit_burst
        self._timeout_start_sec = timeout_start_sec
        self._exit_on_failure = exit_on_failure
        self._func_name = func.__name__
        self._func = func
        self._task: asyncio.Task[R | None] | None = None
        self._status = TaskStatus.NOT_RUNNING
        self._result: R | None = None

        if not current_event_loop_exists():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        else:
            self._loop = asyncio.get_event_loop()

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

            exception = None
            try:
                exception = task.exception()
            except asyncio.CancelledError:
                return

            if exception is not None:
                logger.error(
                    "Task '%s' encountered an exception: %r",
                    self._func_name,
                    exception,
                )
                os.kill(os.getpid(), signal.SIGTERM)
            else:
                self._result = task.result()

        async def run_task() -> R | None:
            if inspect.iscoroutinefunction(self._func):
                logger.info("Starting task %r", self._func_name)
                self._status = TaskStatus.RUNNING
                attempts = 0
                start_time = None

                if self._timeout_start_sec:
                    # Wait for timeout_start_sec seconds
                    await asyncio.sleep(self._timeout_start_sec)

                while True:
                    res: Coroutine[None, None, R | None] = self._func()

                    try:
                        await res
                    except asyncio.CancelledError:
                        logger.info("Task '%s' was cancelled", self._func_name)
                        raise
                    except Exception as e:
                        if start_time is None:
                            start_time = time()

                        attempts += 1
                        logger.exception(
                            "Task %r encountered an exception: %r [attempt %s since %s].",
                            self._func.__name__,
                            e,
                            attempts,
                            datetime.fromtimestamp(start_time),
                        )
                        if not self._restart_on_failure:
                            if self._exit_on_failure:
                                raise e
                            break
                        if self._start_limit_interval_sec is not None:
                            if (time() - start_time) > self._start_limit_interval_sec:
                                # reset attempts if start_limit_interval_sec is exceeded
                                start_time = time()
                                attempts = 1
                            elif attempts > self._start_limit_burst:
                                logger.error(
                                    "Task %r exceeded restart burst limit. Stopping.",
                                    self._func.__name__,
                                )
                                if self._exit_on_failure:
                                    raise e
                                break
                        await asyncio.sleep(self._restart_sec)
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
