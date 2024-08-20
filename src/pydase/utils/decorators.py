import inspect
from collections.abc import Callable
from typing import Any

from pydase.utils.helpers import function_has_arguments


class FunctionDefinitionError(Exception):
    pass


def frontend(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to mark a [`DataService`][pydase.DataService] method for frontend
    rendering. Ensures that the method does not contain arguments, as they are not
    supported for frontend rendering.
    """

    if function_has_arguments(func):
        raise FunctionDefinitionError(
            "The @frontend decorator requires functions without arguments. Function "
            f"'{func.__name__}' has at least one argument. "
            "Please remove the argument(s) from this function to use it with the "
            "@frontend decorator."
        )

    # Mark the function for frontend display.
    func._display_in_frontend = True  # type: ignore
    return func


def render_in_frontend(func: Callable[..., Any]) -> bool:
    """Determines if the method should be rendered in the frontend.

    It checks if the "@frontend" decorator was used or the method is a coroutine."""

    if inspect.iscoroutinefunction(func):
        return True

    try:
        return func._display_in_frontend  # type: ignore
    except AttributeError:
        return False
