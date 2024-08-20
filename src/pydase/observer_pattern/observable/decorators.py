import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

if TYPE_CHECKING:
    from pydase.observer_pattern.observable.observable import Observable

P = ParamSpec("P")
R = TypeVar("R")


def validate_set(
    *, timeout: float = 0.1, precision: float | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator marking a property setter to read back the set value using the property
    getter and check against the desired value.

    Args:
        timeout:
            The maximum time (in seconds) to wait for the value to be within the
            precision boundary.
        precision:
            The acceptable deviation from the desired value. If None, the value must be
            exact.
    """

    def validate_set_decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        wrapper._validate_kwargs = {  # type: ignore
            "timeout": timeout,
            "precision": precision,
        }

        return wrapper

    return validate_set_decorator


def has_validate_set_decorator(prop: property) -> bool:
    """
    Checks if a property setter has been decorated with the `validate_set` decorator.

    Args:
        prop:
            The property to check.

    Returns:
        True if the property setter has the `validate_set` decorator, False otherwise.
    """

    property_setter = prop.fset
    return hasattr(property_setter, "_validate_kwargs")


def _validate_value_was_correctly_set(
    *,
    obj: "Observable",
    name: str,
    value: Any,
) -> None:
    """
    Validates if the property `name` of `obj` attains the desired `value` within the
    specified `precision` and time `timeout`.

    Args:
        obj:
            The instance of the class containing the property.
        name:
            The name of the property to validate.
        value:
            The desired value to check against.

    Raises:
        ValueError:
            If the property value does not match the desired value within the specified
            precision and timeout.
    """

    prop: property = getattr(type(obj), name)

    timeout = prop.fset._validate_kwargs["timeout"]  # type: ignore
    precision = prop.fset._validate_kwargs["precision"]  # type: ignore
    if precision is None:
        precision = 0.0

    start_time = time.time()
    while time.time() - start_time < timeout:
        current_value = obj.__getattribute__(name)
        # This check is faster than rounding and comparing to 0
        if abs(current_value - value) <= precision:
            return
        time.sleep(0.01)
    raise ValueError(
        f"Failed to set value to {value} within {timeout} seconds. Current value: "
        f"{current_value}."
    )
