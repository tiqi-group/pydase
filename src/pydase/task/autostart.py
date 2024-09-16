from typing import Any

import pydase.data_service.data_service
import pydase.task.task
from pydase.task.task_status import TaskStatus
from pydase.utils.helpers import is_property_attribute


def autostart_service_tasks(
    service: pydase.data_service.data_service.DataService,
) -> None:
    """Starts the service tasks defined with the `autostart` keyword argument.

    This method goes through the attributes of the passed service and its nested
    [`DataService`][pydase.DataService] instances and calls the start method on
    autostart-tasks.
    """

    for attr in dir(service):
        if is_property_attribute(service, attr):  # prevent eval of property attrs
            continue

        val = getattr(service, attr)
        if (
            isinstance(val, pydase.task.task.Task)
            and val.autostart
            and val.status == TaskStatus.NOT_RUNNING
        ):
            val.start()
        else:
            autostart_nested_service_tasks(val)


def autostart_nested_service_tasks(
    service: pydase.data_service.data_service.DataService | list[Any] | dict[Any, Any],
) -> None:
    if isinstance(service, pydase.DataService):
        autostart_service_tasks(service)
    elif isinstance(service, list):
        for entry in service:
            autostart_service_tasks(entry)
    elif isinstance(service, dict):
        for entry in service.values():
            autostart_service_tasks(entry)
