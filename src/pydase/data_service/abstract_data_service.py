from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydase.observer_pattern.observable.observable import Observable

if TYPE_CHECKING:
    from pydase.data_service.data_service import DataService
    from pydase.data_service.task_manager import TaskManager


class AbstractDataService(Observable):
    __root__: DataService
    _task_manager: TaskManager
    _autostart_tasks: dict[str, tuple[Any]]
