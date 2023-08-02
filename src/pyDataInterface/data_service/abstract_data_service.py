from abc import ABC
from collections.abc import Callable
from typing import Any


class AbstractDataService(ABC):
    __root__: "AbstractDataService"
    _callback_manager: Any
    """
    This is a CallbackManager. Cannot type this here as this would lead to a recursive
    loop.
    """

    _task_status_change_callbacks: list[Callable[[str, dict[str, Any] | None], None]]
