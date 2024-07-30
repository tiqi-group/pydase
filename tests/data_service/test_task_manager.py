import asyncio
import logging

import pydase
import pytest
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pytest import LogCaptureFixture

logger = logging.getLogger("pydase")


@pytest.mark.asyncio(scope="function")
async def test_autostart_task_callback(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._autostart_tasks = {  # type: ignore
                "my_task": (),  # type: ignore
                "my_other_task": (),  # type: ignore
            }

        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    # Your test code here
    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance._task_manager.start_autostart_tasks()

    assert "'my_task' changed to 'TaskStatus.RUNNING'" in caplog.text
    assert "'my_other_task' changed to 'TaskStatus.RUNNING'" in caplog.text


@pytest.mark.asyncio(scope="function")
async def test_DataService_subclass_autostart_task_callback(
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

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance._task_manager.start_autostart_tasks()

    assert "'sub_service.my_task' changed to 'TaskStatus.RUNNING'" in caplog.text
    assert "'sub_service.my_other_task' changed to 'TaskStatus.RUNNING'" in caplog.text


@pytest.mark.asyncio(scope="function")
async def test_DataService_subclass_list_autostart_task_callback(
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

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance._task_manager.start_autostart_tasks()

    assert (
        "'sub_services_list[0].my_task' changed to 'TaskStatus.RUNNING'" in caplog.text
    )
    assert (
        "'sub_services_list[0].my_other_task' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )
    assert (
        "'sub_services_list[1].my_task' changed to 'TaskStatus.RUNNING'" in caplog.text
    )
    assert (
        "'sub_services_list[1].my_other_task' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )


@pytest.mark.asyncio(scope="function")
async def test_start_and_stop_task_methods(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()

        async def my_task(self) -> None:
            while True:
                logger.debug("Logging message")
                await asyncio.sleep(0.1)

    # Your test code here
    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance.start_my_task()
    await asyncio.sleep(0.01)

    assert "'my_task' changed to 'TaskStatus.RUNNING'" in caplog.text
    assert "Logging message" in caplog.text
    caplog.clear()

    service_instance.stop_my_task()
    await asyncio.sleep(0.01)
    assert "Task 'my_task' was cancelled" in caplog.text
