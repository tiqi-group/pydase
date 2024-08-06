import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from pydase.task.task import Task

logger = logging.getLogger(__name__)

R = TypeVar("R")


def task(
    *, autostart: bool = False
) -> Callable[[Callable[[Any], Coroutine[None, None, R]]], Task[R]]:
    def decorator(
        func: Callable[[Any], Coroutine[None, None, R]],
    ) -> Task[R]:
        @functools.wraps(func)
        async def wrapper(self: Any) -> R | None:
            try:
                return await func(self)
            except asyncio.CancelledError:
                logger.info("Task '%s' was cancelled", func.__name__)
                return None

        return Task(wrapper, autostart=autostart)

    return decorator
