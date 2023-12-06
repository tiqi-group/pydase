from typing import Any

import pydase.units as u
from pydase.data_service.data_service import DataService
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pytest import LogCaptureFixture


def test_DataService_setattr(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        voltage = 1.0 * u.units.V
        _current: u.Quantity = 1.0 * u.units.mA

        @property
        def current(self) -> u.Quantity:
            return self._current

        @current.setter
        def current(self, value: Any) -> None:
            self._current = value

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.voltage = 10.0 * u.units.V
    service_instance.current = 1.5 * u.units.mA

    assert "'voltage' changed to '10.0 V'" in caplog.text
    assert "'current' changed to '1.5 mA'" in caplog.text

    assert service_instance.voltage == 10.0 * u.units.V
    assert service_instance.current == 1.5 * u.units.mA
    caplog.clear()

    service_instance.voltage = 12.0 * u.units.V
    service_instance.current = 1.51 * u.units.A

    assert "'voltage' changed to '12.0 V'" in caplog.text
    assert "'current' changed to '1.51 A'" in caplog.text

    assert service_instance.voltage == 12.0 * u.units.V
    assert service_instance.current == 1.51 * u.units.A


def test_convert_to_quantity() -> None:
    assert u.convert_to_quantity(1.0, unit="V") == 1.0 * u.units.V
    assert u.convert_to_quantity(1, unit="mV") == 1.0 * u.units.mV
    assert u.convert_to_quantity({"magnitude": 12, "unit": "kV"}) == 12.0 * u.units.kV
    assert u.convert_to_quantity(1.0 * u.units.mV) == 1.0 * u.units.mV


def test_set_service_attribute_value_by_path(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        voltage = 1.0 * u.units.V
        _current: u.Quantity = 1.0 * u.units.mA

        @property
        def current(self) -> u.Quantity:
            return self._current

        @current.setter
        def current(self, value: Any) -> None:
            self._current = value

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    state_manager.set_service_attribute_value_by_path(
        path="voltage", value=1.0 * u.units.mV
    )
    assert "'voltage' changed to '1.0 mV'" in caplog.text
    caplog.clear()

    state_manager.set_service_attribute_value_by_path(path="voltage", value=2)

    assert "'voltage' changed to '2.0 mV'" in caplog.text
    caplog.clear()

    state_manager.set_service_attribute_value_by_path(
        path="voltage", value={"magnitude": 123, "unit": "kV"}
    )
    assert "'voltage' changed to '123.0 kV'" in caplog.text


def test_autoconvert_offset_to_baseunit() -> None:
    import pint

    assert u.units.autoconvert_offset_to_baseunit is True

    try:
        quantity = 10 * u.units.degC
    except pint.errors.OffsetUnitCalculusError as exc:
        assert False, f"Offset unit raises exception {exc}"


def test_loading_from_json(caplog: LogCaptureFixture) -> None:
    """This function tests if the quantity read from the json description is actually
    passed as a quantity to the property setter."""
    JSON_DICT = {
        "some_unit": {
            "type": "Quantity",
            "value": {"magnitude": 10.0, "unit": "A"},
            "readonly": False,
            "doc": None,
        }
    }

    class ServiceClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self._unit: u.Quantity = 1 * u.units.A

        @property
        def some_unit(self) -> u.Quantity:
            return self._unit

        @some_unit.setter
        def some_unit(self, value: u.Quantity) -> None:
            assert isinstance(value, u.Quantity)
            self._unit = value

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.load_DataService_from_JSON(JSON_DICT)

    assert "'some_unit' changed to '10.0 A'" in caplog.text
