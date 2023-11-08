import json
from pathlib import Path
from typing import Any

from pytest import LogCaptureFixture

import pydase
import pydase.units as u
from pydase.data_service.state_manager import StateManager


class SubService(pydase.DataService):
    name = "SubService"


class Service(pydase.DataService):
    def __init__(self, **kwargs: Any) -> None:
        self.subservice = SubService()
        self.some_unit: u.Quantity = 1.2 * u.units.A
        self.some_float = 1.0
        self._name = "Service"
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return self._name


CURRENT_STATE = Service().serialize()

LOAD_STATE = {
    "name": {
        "type": "str",
        "value": "Another name",
        "readonly": True,
        "doc": None,
    },
    "some_float": {
        "type": "int",
        "value": 10,
        "readonly": False,
        "doc": None,
    },
    "some_unit": {
        "type": "Quantity",
        "value": {"magnitude": 12.0, "unit": "A"},
        "readonly": False,
        "doc": None,
    },
    "subservice": {
        "type": "DataService",
        "value": {
            "name": {
                "type": "str",
                "value": "SubService",
                "readonly": False,
                "doc": None,
            }
        },
        "readonly": False,
        "doc": None,
    },
    "removed_attr": {
        "type": "str",
        "value": "removed",
        "readonly": False,
        "doc": None,
    },
}


def test_save_state(tmp_path: Path):
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"
    manager = StateManager(service=Service(), filename=str(file))

    # Trigger the saving action
    manager.save_state()

    # Now check that the file was written correctly
    assert file.read_text() == json.dumps(CURRENT_STATE, indent=4)


def test_load_state(tmp_path: Path, caplog: LogCaptureFixture):
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"

    # Write a temporary JSON file to read back
    with open(file, "w") as f:
        json.dump(LOAD_STATE, f, indent=4)

    service = Service()
    manager = StateManager(service=service, filename=str(file))
    manager.load_state()

    assert service.some_unit == u.Quantity(12, "A")  # has changed
    assert service.name == "Service"  # has not changed as readonly
    assert service.some_float == 1.0  # has not changed due to different type
    assert service.some_float == 1.0  # has not changed due to different type
    assert service.subservice.name == "SubService"  # didn't change

    assert "Service.some_unit changed to 12.0 A!" in caplog.text
    assert (
        "Attribute 'name' is read-only. Ignoring value from JSON file..." in caplog.text
    )
    assert (
        "Attribute type of 'some_float' changed from 'int' to 'float'. "
        "Ignoring value from JSON file..."
    ) in caplog.text
    assert (
        "Attribute type of 'removed_attr' changed from 'str' to None. "
        "Ignoring value from JSON file..." in caplog.text
    )
    assert "Value of attribute 'subservice.name' has not changed..." in caplog.text


def test_filename_warning(tmp_path: Path, caplog: LogCaptureFixture):
    file = tmp_path / "test_state.json"

    service = Service(filename=str(file))
    StateManager(service=service, filename=str(file))
    assert f"Overwriting filename {str(file)!r} with {str(file)!r}." in caplog.text


def test_filename_error(caplog: LogCaptureFixture):
    service = Service()
    manager = StateManager(service=service)

    manager.save_state()
    assert (
        "State manager was not initialised with a filename. Skipping 'save_state'..."
        in caplog.text
    )


def test_readonly_attribute(tmp_path: Path, caplog: LogCaptureFixture):
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"

    # Write a temporary JSON file to read back
    with open(file, "w") as f:
        json.dump(LOAD_STATE, f, indent=4)

    service = Service()
    manager = StateManager(service=service, filename=str(file))
    manager.load_state()
    assert (
        "Attribute 'name' is read-only. Ignoring value from JSON file..." in caplog.text
    )


def test_changed_type(tmp_path: Path, caplog: LogCaptureFixture):
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"

    # Write a temporary JSON file to read back
    with open(file, "w") as f:
        json.dump(LOAD_STATE, f, indent=4)

    service = Service()
    manager = StateManager(service=service, filename=str(file))
    manager.load_state()
    assert (
        "Attribute type of 'some_float' changed from 'int' to "
        "'float'. Ignoring value from JSON file..."
    ) in caplog.text
