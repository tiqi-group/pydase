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


@pytest.mark.asyncio(scope="function")
async def test_manual_start_with_multiple_service_instances(
    caplog: LogCaptureFixture,
) -> None:
    class MySubService(pydase.DataService):
        @task()
        async def my_task(self) -> None:
            logger.info("Triggered task.")
            while True:
                await asyncio.sleep(1)

    class MyService(pydase.DataService):
        sub_services_list = [MySubService() for i in range(2)]
        sub_services_dict = {"first": MySubService(), "second": MySubService()}

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    autostart_service_tasks(service_instance)

    await asyncio.sleep(0.1)

    assert (
        service_instance.sub_services_list[0].my_task.status == TaskStatus.NOT_RUNNING
    )
    assert (
        service_instance.sub_services_list[1].my_task.status == TaskStatus.NOT_RUNNING
    )
    assert (
        service_instance.sub_services_dict["first"].my_task.status
        == TaskStatus.NOT_RUNNING
    )
    assert (
        service_instance.sub_services_dict["second"].my_task.status
        == TaskStatus.NOT_RUNNING
    )

    service_instance.sub_services_list[0].my_task.start()
    await asyncio.sleep(0.01)

    assert service_instance.sub_services_list[0].my_task.status == TaskStatus.RUNNING
    assert (
        "'sub_services_list[0].my_task.status' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )
    assert (
        "'sub_services_list[1].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_dict[\"first\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_dict[\"second\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )

    service_instance.sub_services_list[0].my_task.stop()
    await asyncio.sleep(0.01)

    assert "Task 'my_task' was cancelled" in caplog.text
    caplog.clear()

    service_instance.sub_services_list[1].my_task.start()
    await asyncio.sleep(0.01)

    assert service_instance.sub_services_list[1].my_task.status == TaskStatus.RUNNING
    assert (
        "'sub_services_list[0].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_list[1].my_task.status' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )
    assert (
        "'sub_services_dict[\"first\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_dict[\"second\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )

    service_instance.sub_services_list[1].my_task.stop()
    await asyncio.sleep(0.01)

    assert "Task 'my_task' was cancelled" in caplog.text
    caplog.clear()

    service_instance.sub_services_dict["first"].my_task.start()
    await asyncio.sleep(0.01)

    assert (
        service_instance.sub_services_dict["first"].my_task.status == TaskStatus.RUNNING
    )
    assert (
        "'sub_services_list[0].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_list[1].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_dict[\"first\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )
    assert (
        "'sub_services_dict[\"second\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )

    service_instance.sub_services_dict["first"].my_task.stop()
    await asyncio.sleep(0.01)

    assert "Task 'my_task' was cancelled" in caplog.text
    caplog.clear()

    service_instance.sub_services_dict["second"].my_task.start()
    await asyncio.sleep(0.01)

    assert (
        service_instance.sub_services_dict["second"].my_task.status
        == TaskStatus.RUNNING
    )
    assert (
        "'sub_services_list[0].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_list[1].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_dict[\"first\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        not in caplog.text
    )
    assert (
        "'sub_services_dict[\"second\"].my_task.status' changed to 'TaskStatus.RUNNING'"
        in caplog.text
    )

    service_instance.sub_services_dict["second"].my_task.stop()
    await asyncio.sleep(0.01)

    assert "Task 'my_task' was cancelled" in caplog.text


@pytest.mark.asyncio(scope="function")
async def test_restart_on_exception(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        @task(restart_on_exception=True, restart_sec=0.1)
        async def my_task(self) -> None:
            logger.info("Triggered task.")
            raise Exception("Task failure")

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance.my_task.start()

    await asyncio.sleep(0.01)
    assert "Task 'my_task' encountered an exception" in caplog.text
    caplog.clear()
    await asyncio.sleep(0.1)
    assert service_instance.my_task.status == TaskStatus.RUNNING
    assert "Task 'my_task' encountered an exception" in caplog.text
    assert "Triggered task." in caplog.text


@pytest.mark.asyncio(scope="function")
async def test_restart_sec(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        @task(restart_on_exception=True, restart_sec=0.1)
        async def my_task(self) -> None:
            logger.info("Triggered task.")
            raise Exception("Task failure")

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance.my_task.start()

    await asyncio.sleep(0.001)
    assert "Triggered task." in caplog.text
    caplog.clear()
    await asyncio.sleep(0.05)
    assert "Triggered task." not in caplog.text
    await asyncio.sleep(0.05)
    assert "Triggered task." in caplog.text  # Ensures the task restarted after 0.2s


@pytest.mark.asyncio(scope="function")
async def test_exceeding_start_limit_interval_sec_and_burst(
    caplog: LogCaptureFixture,
) -> None:
    class MyService(pydase.DataService):
        @task(
            restart_on_exception=True,
            restart_sec=0.0,
            start_limit_interval_sec=1.0,
            start_limit_burst=2,
        )
        async def my_task(self) -> None:
            raise Exception("Task failure")

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance.my_task.start()

    await asyncio.sleep(0.1)
    assert "Task 'my_task' exceeded restart burst limit" in caplog.text
    assert service_instance.my_task.status == TaskStatus.NOT_RUNNING


@pytest.mark.asyncio(scope="function")
async def test_non_exceeding_start_limit_interval_sec_and_burst(
    caplog: LogCaptureFixture,
) -> None:
    class MyService(pydase.DataService):
        @task(
            restart_on_exception=True,
            restart_sec=0.1,
            start_limit_interval_sec=0.1,
            start_limit_burst=2,
        )
        async def my_task(self) -> None:
            raise Exception("Task failure")

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance.my_task.start()

    await asyncio.sleep(0.5)
    assert "Task 'my_task' exceeded restart burst limit" not in caplog.text
    assert service_instance.my_task.status == TaskStatus.RUNNING


@pytest.mark.asyncio(scope="function")
async def test_exit_on_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: LogCaptureFixture
) -> None:
    class MyService(pydase.DataService):
        @task(restart_on_exception=False, exit_on_failure=True)
        async def my_task(self) -> None:
            logger.info("Triggered task.")
            raise Exception("Critical failure")

    def mock_os_kill(pid: int, signal: int) -> None:
        logger.critical("os.kill called with signal=%s and pid=%s", signal, pid)

    monkeypatch.setattr("os.kill", mock_os_kill)

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance.my_task.start()

    await asyncio.sleep(0.1)
    assert "os.kill called with signal=" in caplog.text
    assert "Task 'my_task' encountered an exception" in caplog.text


@pytest.mark.asyncio(scope="function")
async def test_exit_on_failure_exceeding_rate_limit(
    monkeypatch: pytest.MonkeyPatch, caplog: LogCaptureFixture
) -> None:
    class MyService(pydase.DataService):
        @task(
            restart_on_exception=True,
            restart_sec=0.0,
            start_limit_interval_sec=0.1,
            start_limit_burst=2,
            exit_on_failure=True,
        )
        async def my_task(self) -> None:
            raise Exception("Critical failure")

    def mock_os_kill(pid: int, signal: int) -> None:
        logger.critical("os.kill called with signal=%s and pid=%s", signal, pid)

    monkeypatch.setattr("os.kill", mock_os_kill)

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance.my_task.start()

    await asyncio.sleep(0.5)
    assert "os.kill called with signal=" in caplog.text
    assert "Task 'my_task' encountered an exception" in caplog.text
