import logging

from pytest import CaptureFixture

import pydase

logger = logging.getLogger()


def test_autostart_task_callback(capsys: CaptureFixture) -> None:
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

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "MyService.my_task = {}",
            "MyService.my_other_task = {}",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert expected_output == actual_output


def test_DataService_subclass_autostart_task_callback(capsys: CaptureFixture) -> None:
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

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "MyService.sub_service.my_task = {}",
            "MyService.sub_service.my_other_task = {}",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert expected_output == actual_output


def test_DataServiceList_subclass_autostart_task_callback(
    capsys: CaptureFixture,
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

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "MyService.sub_services_list[0].my_task = {}",
            "MyService.sub_services_list[0].my_other_task = {}",
            "MyService.sub_services_list[1].my_task = {}",
            "MyService.sub_services_list[1].my_other_task = {}",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert expected_output == actual_output
