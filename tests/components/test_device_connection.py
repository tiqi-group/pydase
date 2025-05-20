import asyncio

import pydase
import pydase.components.device_connection
import pytest
from pydase.task.autostart import autostart_service_tasks
from pytest import LogCaptureFixture


@pytest.mark.asyncio(loop_scope="function")
async def test_reconnection(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.components.device_connection.DeviceConnection):
        def __init__(
            self,
        ) -> None:
            super().__init__()
            self._reconnection_wait_time = 0.01

        def connect(self) -> None:
            self._connected = True

    service_instance = MyService()
    autostart_service_tasks(service_instance)

    assert service_instance._connected is False

    await asyncio.sleep(0.01)
    assert service_instance._connected is True
