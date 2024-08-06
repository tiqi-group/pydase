import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any, Concatenate, ParamSpec, TypeVar

from pydase.task.task import Task

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def task(
    *, autostart: bool = False
) -> Callable[[Callable[Concatenate[Any, P], Coroutine[None, None, R]]], Task[P, R]]:
    def decorator(
        func: Callable[Concatenate[Any, P], Coroutine[None, None, R]],
    ) -> Task[P, R]:
        @functools.wraps(func)
        async def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> R | None:
            try:
                return await func(self, *args, **kwargs)
            except asyncio.CancelledError:
                logger.info("Task '%s' was cancelled", func.__name__)
                return None

        return Task(wrapper, autostart=autostart)

    return decorator
