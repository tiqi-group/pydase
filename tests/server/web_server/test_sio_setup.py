import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

# Assuming your code is in a file named 'socket_server.py'
from pydase.server.web_server.sio_setup import (
    RunMethodDict,
    UpdateDict,
    setup_sio_server,
)

logger = logging.getLogger(__name__)


# Mocks
class MockObserver:
    def __init__(self) -> None:
        self.state_manager = MagicMock()
        self.add_notification_callback = MagicMock()

        # Create a mock service with a mock method
        mock_service = MagicMock()
        mock_service.test_method = lambda: logger.info("Triggered 'test_method'.")

        # Assign the mock service to the state manager
        self.state_manager.service = mock_service


class MockServer:
    def __init__(self) -> None:
        self.emit = AsyncMock()


@pytest.fixture
def mock_observer() -> MockObserver:
    return MockObserver()


@pytest.fixture
def mock_sio() -> MagicMock:
    return MagicMock()


@pytest.mark.asyncio
async def test_set_attribute_event(mock_observer: MockObserver) -> None:
    server = setup_sio_server(mock_observer, False, asyncio.get_running_loop())

    test_sid = 1234
    test_data: UpdateDict = {
        "parent_path": "test.parent.path",
        "name": "test_attr",
        "value": "new_value",
    }

    server.handlers["/"]["set_attribute"](test_sid, test_data)

    mock_observer.state_manager.set_service_attribute_value_by_path.assert_called_with(
        path="test.parent.path.test_attr", value="new_value"
    )


@pytest.mark.asyncio
async def test_run_method_event(mock_observer, caplog: pytest.LogCaptureFixture):
    server = setup_sio_server(mock_observer, False, asyncio.get_running_loop())

    test_sid = 1234
    test_data: RunMethodDict = {
        "parent_path": "",
        "name": "test_method",
        "kwargs": {},
    }

    server.handlers["/"]["run_method"](test_sid, test_data)

    assert "Triggered 'test_method'." in caplog.text
