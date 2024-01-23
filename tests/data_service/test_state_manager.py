import json
from pathlib import Path
from typing import Any

import pydase
import pydase.components
import pydase.units as u
import pytest
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import (
    StateManager,
    has_load_state_decorator,
    load_state,
)
from pytest import LogCaptureFixture


class SubService(pydase.DataService):
    name = "SubService"


class State(pydase.components.ColouredEnum):
    RUNNING = "#0000FF80"
    COMPLETED = "hsl(120, 100%, 50%)"
    FAILED = "hsla(0, 100%, 50%, 0.7)"


class MySlider(pydase.components.NumberSlider):
    @property
    def min(self) -> float:
        return self._min

    @min.setter
    @load_state
    def min(self, value: float) -> None:
        self._min = value

    @property
    def max(self) -> float:
        return self._max

    @max.setter
    @load_state
    def max(self, value: float) -> None:
        self._max = value

    @property
    def step_size(self) -> float:
        return self._step_size

    @step_size.setter
    @load_state
    def step_size(self, value: float) -> None:
        self._step_size = value

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    @load_state
    def value(self, value: float) -> None:
        if value < self._min or value > self._max:
            raise ValueError("Value is either below allowed min or above max value.")

        self._value = value


class Service(pydase.DataService):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.subservice = SubService()
        self.some_unit: u.Quantity = 1.2 * u.units.A
        self.some_float = 1.0
        self.list_attr = [1.0, 2.0]
        self._property_attr = 1337.0
        self._name = "Service"
        self.state = State.RUNNING
        self.my_slider = MySlider()

    @property
    def name(self) -> str:
        return self._name

    @property
    def property_attr(self) -> float:
        return self._property_attr

    @property_attr.setter
    def property_attr(self, value: float) -> None:
        self._property_attr = value


CURRENT_STATE = Service().serialize()["value"]

LOAD_STATE = {
    "list_attr": {
        "type": "list",
        "value": [
            {"type": "float", "value": 1.4, "readonly": False, "doc": None},
            {"type": "float", "value": 2.0, "readonly": False, "doc": None},
        ],
        "readonly": False,
        "doc": None,
    },
    "my_slider": {
        "type": "NumberSlider",
        "value": {
            "max": {
                "type": "float",
                "value": 101.0,
                "readonly": False,
                "doc": "The min property.",
            },
            "min": {
                "type": "float",
                "value": 1.0,
                "readonly": False,
                "doc": "The min property.",
            },
            "step_size": {
                "type": "float",
                "value": 2.0,
                "readonly": False,
                "doc": "The min property.",
            },
            "value": {
                "type": "float",
                "value": 1.0,
                "readonly": False,
                "doc": "The value property.",
            },
        },
        "readonly": False,
        "doc": None,
    },
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
    "state": {
        "type": "ColouredEnum",
        "value": "FAILED",
        "readonly": True,
        "doc": None,
        "enum": {
            "RUNNING": "#0000FF80",
            "COMPLETED": "hsl(120, 100%, 50%)",
            "FAILED": "hsla(0, 100%, 50%, 0.7)",
        },
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


def test_save_state(tmp_path: Path) -> None:
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"
    manager = StateManager(service=Service(), filename=str(file))

    # Trigger the saving action
    manager.save_state()

    # Now check that the file was written correctly
    assert file.read_text() == json.dumps(CURRENT_STATE, indent=4)


def test_load_state(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"

    # Write a temporary JSON file to read back
    with open(file, "w") as f:
        json.dump(LOAD_STATE, f, indent=4)

    service = Service()
    state_manager = StateManager(service=service, filename=str(file))
    DataServiceObserver(state_manager)
    state_manager.load_state()

    assert service.some_unit == u.Quantity(12, "A")  # has changed
    assert service.list_attr[0] == 1.4  # has changed
    assert service.list_attr[1] == 2.0  # has not changed
    assert (
        service.property_attr == 1337
    )  # has not changed as property has not @load_state decorator
    assert service.state == State.FAILED  # has changed
    assert service.name == "Service"  # has not changed as readonly
    assert service.some_float == 1.0  # has not changed due to different type
    assert service.subservice.name == "SubService"  # didn't change
    assert service.my_slider.value == 1.0  # changed
    assert service.my_slider.min == 1.0  # changed
    assert service.my_slider.max == 101.0  # changed
    assert service.my_slider.step_size == 2.0  # changed

    assert "'some_unit' changed to '12.0 A'" in caplog.text
    assert (
        "Property 'name' has no '@load_state' decorator. "
        "Ignoring value from JSON file..." in caplog.text
    )
    assert (
        "Attribute type of 'some_float' changed from 'int' to 'float'. "
        "Ignoring value from JSON file..."
    ) in caplog.text
    assert (
        "Attribute type of 'removed_attr' changed from 'str' to 'None'. "
        "Ignoring value from JSON file..." in caplog.text
    )
    assert "Value of attribute 'subservice.name' has not changed..." in caplog.text
    assert "'my_slider.value' changed to '1.0'" in caplog.text
    assert "'my_slider.min' changed to '1.0'" in caplog.text
    assert "'my_slider.max' changed to '101.0'" in caplog.text
    assert "'my_slider.step_size' changed to '2.0'" in caplog.text


def test_filename_warning(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    file = tmp_path / "test_state.json"

    with pytest.warns(DeprecationWarning):
        service = Service(filename=str(file))
        StateManager(service=service, filename=str(file))

    assert f"Overwriting filename {str(file)!r} with {str(file)!r}." in caplog.text


def test_filename_error(caplog: LogCaptureFixture) -> None:
    service = Service()
    manager = StateManager(service=service)

    manager.save_state()
    assert (
        "State manager was not initialised with a filename. Skipping 'save_state'..."
        in caplog.text
    )


def test_readonly_attribute(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"

    # Write a temporary JSON file to read back
    with open(file, "w") as f:
        json.dump(LOAD_STATE, f, indent=4)

    service = Service()
    manager = StateManager(service=service, filename=str(file))
    manager.load_state()
    assert service.name == "Service"
    assert (
        "Property 'name' has no '@load_state' decorator. "
        "Ignoring value from JSON file..." in caplog.text
    )


def test_changed_type(tmp_path: Path, caplog: LogCaptureFixture) -> None:
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


def test_property_load_state(tmp_path: Path) -> None:
    # Create a StateManager instance with a temporary file
    file = tmp_path / "test_state.json"

    LOAD_STATE = {
        "name": {
            "type": "str",
            "value": "Some other name",
            "readonly": False,
            "doc": None,
        },
        "not_loadable_attr": {
            "type": "str",
            "value": "But I AM loadable!?",
            "readonly": False,
            "doc": None,
        },
    }

    # Write a temporary JSON file to read back
    with open(file, "w") as f:
        json.dump(LOAD_STATE, f, indent=4)

    class Service(pydase.DataService):
        _name = "Service"
        _not_loadable_attr = "Not loadable"

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        @load_state
        def name(self, value: str) -> None:
            self._name = value

        @property
        def not_loadable_attr(self) -> str:
            return self._not_loadable_attr

        @not_loadable_attr.setter
        def not_loadable_attr(self, value: str) -> None:
            self._not_loadable_attr = value

        @property
        def property_without_setter(self) -> None:
            return

    service_instance = Service()
    StateManager(service_instance, filename=file).load_state()

    assert service_instance.name == "Some other name"
    assert service_instance.not_loadable_attr == "Not loadable"
    assert not has_load_state_decorator(type(service_instance).property_without_setter)
