import logging

from pytest import LogCaptureFixture

import pydase

logger = logging.getLogger()


def test_autostart_task_callback(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        def __init__(self) -> None:
            self._autostart_tasks = {  # type: ignore
                "my_task": (),
                "my_other_task": (),
            }
            super().__init__()

        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    service = MyService()
    service._task_manager.start_autostart_tasks()

    assert "MyService.my_task changed to {}" in caplog.text
    assert "MyService.my_other_task changed to {}" in caplog.text


def test_DataService_subclass_autostart_task_callback(
    caplog: LogCaptureFixture,
) -> None:
    class MySubService(pydase.DataService):
        def __init__(self) -> None:
            self._autostart_tasks = {  # type: ignore
                "my_task": (),
                "my_other_task": (),
            }
            super().__init__()

        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    class MyService(pydase.DataService):
        sub_service = MySubService()

    service = MyService()
    service._task_manager.start_autostart_tasks()

    assert "MyService.sub_service.my_task changed to {}" in caplog.text
    assert "MyService.sub_service.my_other_task changed to {}" in caplog.text


def test_DataServiceList_subclass_autostart_task_callback(
    caplog: LogCaptureFixture,
) -> None:
    class MySubService(pydase.DataService):
        def __init__(self) -> None:
            self._autostart_tasks = {  # type: ignore
                "my_task": (),
                "my_other_task": (),
            }
            super().__init__()

        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    class MyService(pydase.DataService):
        sub_services_list = [MySubService() for i in range(2)]

    service = MyService()
    service._task_manager.start_autostart_tasks()

    assert "MyService.sub_services_list[0].my_task changed to {}" in caplog.text
    assert "MyService.sub_services_list[0].my_other_task changed to {}" in caplog.text
    assert "MyService.sub_services_list[1].my_task changed to {}" in caplog.text
    assert "MyService.sub_services_list[1].my_other_task changed to {}" in caplog.text
