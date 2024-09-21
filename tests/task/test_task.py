import asyncio
import logging

import pydase
import pytest
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.task.autostart import autostart_service_tasks
from pydase.task.decorator import task
from pydase.task.task_status import TaskStatus
from pytest import LogCaptureFixture

logger = logging.getLogger("pydase")


@pytest.mark.asyncio(scope="function")
async def test_start_and_stop_task(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        @task()
        async def my_task(self) -> None:
            logger.info("Triggered task.")
            while True:
                await asyncio.sleep(1)

    # Your test code here
    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    autostart_service_tasks(service_instance)
    await asyncio.sleep(0.1)
    assert service_instance.my_task.status == TaskStatus.NOT_RUNNING

    service_instance.my_task.start()
    await asyncio.sleep(0.1)
    assert service_instance.my_task.status == TaskStatus.RUNNING

    assert "'my_task.status' changed to 'TaskStatus.RUNNING'" in caplog.text
    assert "Triggered task." in caplog.text
    caplog.clear()

    service_instance.my_task.stop()
    await asyncio.sleep(0.1)
    assert service_instance.my_task.status == TaskStatus.NOT_RUNNING
    assert "Task 'my_task' was cancelled" in caplog.text


@pytest.mark.asyncio(scope="function")
async def test_autostart_task(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        @task(autostart=True)
        async def my_task(self) -> None:
            logger.info("Triggered task.")
            while True:
                await asyncio.sleep(1)

    # Your test code here
    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    autostart_service_tasks(service_instance)

    await asyncio.sleep(0.1)
    assert service_instance.my_task.status == TaskStatus.RUNNING

    assert "'my_task.status' changed to 'TaskStatus.RUNNING'" in caplog.text


@pytest.mark.asyncio(scope="function")
async def test_nested_list_autostart_task(
    caplog: LogCaptureFixture,
) -> None:
    class MySubService(pydase.DataService):
        @task(autostart=True)
        async def my_task(self) -> None:
            logger.info("Triggered task.")
            while True:
                await asyncio.sleep(1)

    class MyService(pydase.DataService):
        sub_services_list = [MySubService() for i in range(2)]

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    autostart_service_tasks(service_instance)

    await asyncio.sleep(0.1)
    assert service_instance.sub_services_list[0].my_task.status == TaskStatus.RUNNING
    assert service_instance.sub_services_list[1].my_task.status == TaskStatus.RUNNING

    assert (
        "'sub_services_list[0].my_task.status' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )
    assert (
        "'sub_services_list[1].my_task.status' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )


@pytest.mark.asyncio(scope="function")
async def test_nested_dict_autostart_task(
    caplog: LogCaptureFixture,
) -> None:
    class MySubService(pydase.DataService):
        @task(autostart=True)
        async def my_task(self) -> None:
            logger.info("Triggered task.")
            while True:
                await asyncio.sleep(1)

    class MyService(pydase.DataService):
        sub_services_dict = {"first": MySubService(), "second": MySubService()}

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    autostart_service_tasks(service_instance)

    await asyncio.sleep(0.1)

    assert (
        service_instance.sub_services_dict["first"].my_task.status == TaskStatus.RUNNING
    )
    assert (
        service_instance.sub_services_dict["second"].my_task.status
        == TaskStatus.RUNNING
    )

    assert (
        "'sub_services_dict[\"first\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )
    assert (
        "'sub_services_dict[\"second\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )
