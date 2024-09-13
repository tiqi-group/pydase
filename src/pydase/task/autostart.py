import pydase.data_service.data_service
import pydase.task.task
from pydase.utils.helpers import is_property_attribute


def autostart_service_tasks(
    service: pydase.data_service.data_service.DataService,
) -> None:
    for attr in dir(service):
        if not is_property_attribute(service, attr):  # prevent eval of property attrs
            val = getattr(service, attr)
            if isinstance(val, pydase.task.task.Task) and val.autostart:
                val.start()
            elif isinstance(val, pydase.DataService):
                autostart_service_tasks(val)
