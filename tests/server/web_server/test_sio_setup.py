import asyncio
import logging

import pydase
import pytest
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.server.web_server.sio_setup import (
    RunMethodDict,
    UpdateDict,
    setup_sio_server,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_set_attribute_event() -> None:
    class SubClass(pydase.DataService):
        name = "SubClass"

    class ServiceClass(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.sub_class = SubClass()

        def some_method(self) -> None:
            logger.info("Triggered 'test_method'.")

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    observer = DataServiceObserver(state_manager)

    server = setup_sio_server(observer, False, asyncio.get_running_loop())

    test_sid = 1234
    test_data: UpdateDict = {
        "parent_path": "sub_class",
        "name": "name",
        "value": "new name",
    }

    server.handlers["/"]["set_attribute"](test_sid, test_data)

    assert service_instance.sub_class.name == "new name"


@pytest.mark.asyncio
async def test_run_method_event(caplog: pytest.LogCaptureFixture):
    class ServiceClass(pydase.DataService):
        def test_method(self) -> None:
            logger.info("Triggered 'test_method'.")

    state_manager = StateManager(ServiceClass())
    observer = DataServiceObserver(state_manager)

    server = setup_sio_server(observer, False, asyncio.get_running_loop())

    test_sid = 1234
    test_data: RunMethodDict = {
        "parent_path": "",
        "name": "test_method",
        "kwargs": {},
    }

    server.handlers["/"]["run_method"](test_sid, test_data)

    assert "Triggered 'test_method'." in caplog.text
