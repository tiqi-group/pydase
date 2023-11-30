import logging

import pydase
from pytest import LogCaptureFixture

logger = logging.getLogger()


def test_autostart_task_callback(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._autostart_tasks = {  # type: ignore
                "my_task": (),
                "my_other_task": (),
            }

        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    service = MyService()
    service._task_manager.start_autostart_tasks()

    assert "'my_task' changed to '{}'" in caplog.text
    assert "'my_other_task' changed to '{}'" in caplog.text


def test_DataService_subclass_autostart_task_callback(
    caplog: LogCaptureFixture,
) -> None:
    class MySubService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._autostart_tasks = {  # type: ignore
                "my_task": (),
                "my_other_task": (),
            }

        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    class MyService(pydase.DataService):
        sub_service = MySubService()

    service = MyService()
    service._task_manager.start_autostart_tasks()

    assert "'sub_service.my_task' changed to '{}'" in caplog.text
    assert "'sub_service.my_other_task' changed to '{}'" in caplog.text


def test_DataServiceList_subclass_autostart_task_callback(
    caplog: LogCaptureFixture,
) -> None:
    class MySubService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._autostart_tasks = {  # type: ignore
                "my_task": (),
                "my_other_task": (),
            }

        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    class MyService(pydase.DataService):
        sub_services_list = [MySubService() for i in range(2)]

    service = MyService()
    service._task_manager.start_autostart_tasks()

    assert "'sub_services_list[0].my_task' changed to '{}'" in caplog.text
    assert "'sub_services_list[0].my_other_task' changed to '{}'" in caplog.text
    assert "'sub_services_list[1].my_task' changed to '{}'" in caplog.text
    assert "'sub_services_list[1].my_other_task' changed to '{}'" in caplog.text
