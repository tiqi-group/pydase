import json
import signal
from pathlib import Path
from typing import Any

import pydase
import pydase.components
import pydase.units as u
from pydase.data_service.state_manager import load_state
from pydase.server.server import Server
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture


def test_signal_handling(mocker: MockerFixture):
    # Mock os._exit and signal.signal
    mock_exit = mocker.patch("os._exit")
    mock_signal = mocker.patch("signal.signal")

    class MyService(pydase.DataService):
        pass

    # Instantiate your server object
    server = pydase.Server(MyService())

    # Call the method to install signal handlers
    server.install_signal_handlers()

    # Check if the signal handlers were registered correctly
    assert mock_signal.call_args_list == [
        mocker.call(signal.SIGINT, server.handle_exit),
        mocker.call(signal.SIGTERM, server.handle_exit),
    ]

    # Simulate receiving a SIGINT signal for the first time
    server.handle_exit(signal.SIGINT, None)
    assert server.should_exit  # assuming should_exit is public
    mock_exit.assert_not_called()

    # Simulate receiving a SIGINT signal for the second time
    server.handle_exit(signal.SIGINT, None)
    mock_exit.assert_called_once_with(1)


class Service(pydase.DataService):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.some_unit: u.Quantity = 1.2 * u.units.A
        self.some_float = 1.0
        self._property_attr = 1337.0

    @property
    def property_attr(self) -> float:
        return self._property_attr

    @property_attr.setter
    @load_state
    def property_attr(self, value: float) -> None:
        self._property_attr = value


CURRENT_STATE = Service().serialize()

LOAD_STATE = {
    "some_float": {
        "type": "float",
        "value": 10.0,
        "readonly": False,
        "doc": None,
    },
    "property_attr": {
        "type": "float",
        "value": 1337.1,
        "readonly": False,
        "doc": None,
    },
    "some_unit": {
        "type": "Quantity",
        "value": {"magnitude": 12.0, "unit": "A"},
        "readonly": False,
        "doc": None,
    },
}


def test_load_state(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"

    # Write a temporary JSON file to read back
    with open(file, "w") as f:
        json.dump(LOAD_STATE, f, indent=4)

    service = Service()
    Server(service, filename=str(file))

    assert service.some_unit == u.Quantity(12, "A")
    assert service.property_attr == 1337.1
    assert service.some_float == 10.0

    assert "'some_unit' changed to '12.0 A'" in caplog.text
    assert "'some_float' changed to '10.0'" in caplog.text
    assert "'property_attr' changed to '1337.1'" in caplog.text
