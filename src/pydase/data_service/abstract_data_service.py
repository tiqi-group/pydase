from __future__ import annotations

import sys
from abc import ABC
from typing import TYPE_CHECKING, Any

if sys.version_info < (3, 9):
    from typing import Dict  # noqa
else:
    Dict = dict


if TYPE_CHECKING:
    from .callback_manager import CallbackManager
    from .data_service import DataService
    from .task_manager import TaskManager


class AbstractDataService(ABC):
    __root__: DataService
    _task_manager: TaskManager
    _callback_manager: CallbackManager
    _autostart_tasks: Dict[str, tuple[Any]]
