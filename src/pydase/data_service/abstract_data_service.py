from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .callback_manager import CallbackManager
    from .data_service import DataService
    from .task_manager import TaskManager


class AbstractDataService(ABC):
    __root__: DataService
    _task_manager: TaskManager
    _callback_manager: CallbackManager
    _autostart_tasks: dict[str, tuple[Any]]
