import logging

from pytest import LogCaptureFixture

import pydase

logger = logging.getLogger()


def test_DataService_task_callback(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    service = MyService()
    service.start_my_task()  # type: ignore
    service.start_my_other_task()  # type: ignore

    assert "MyService.my_task changed to {}" in caplog.text
    assert "MyService.my_other_task changed to {}" in caplog.text


def test_DataServiceList_task_callback(caplog: LogCaptureFixture) -> None:
    class MySubService(pydase.DataService):
        async def my_task(self) -> None:
            logger.info("Triggered task.")

        async def my_other_task(self) -> None:
            logger.info("Triggered other task.")

    class MyService(pydase.DataService):
        sub_services_list = [MySubService() for i in range(2)]

    service = MyService()
    service.sub_services_list[0].start_my_task()  # type: ignore
    service.sub_services_list[1].start_my_other_task()  # type: ignore

    assert "MyService.sub_services_list[0].my_task changed to {}" in caplog.text
    assert "MyService.sub_services_list[1].my_other_task changed to {}" in caplog.text
