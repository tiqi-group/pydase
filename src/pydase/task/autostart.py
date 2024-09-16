import pydase.data_service.data_service
import pydase.task.task
from pydase.utils.helpers import is_property_attribute


def autostart_service_tasks(
    service: pydase.data_service.data_service.DataService,
) -> None:
    """Starts the service tasks defined with the `autostart` keyword argument.

    This method goes through the attributes of the passed service and its nested
    `pydase.DataService` instances and calls the start method on autostart-tasks.
    """

    for attr in dir(service):
        if not is_property_attribute(service, attr):  # prevent eval of property attrs
            val = getattr(service, attr)
            if isinstance(val, pydase.task.task.Task) and val.autostart:
                val.start()
            elif isinstance(val, pydase.DataService):
                autostart_service_tasks(val)
            elif isinstance(val, list):
                for entry in val:
                    autostart_service_tasks(entry)
            elif isinstance(val, dict):
                for entry in val.values():
                    autostart_service_tasks(entry)
