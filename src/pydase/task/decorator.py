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
    def decorator(
        func: Callable[[Any], Coroutine[None, None, R]]
        | Callable[[], Coroutine[None, None, R]],
    ) -> Task[R]:
        return Task(func, autostart=autostart)

    return decorator
