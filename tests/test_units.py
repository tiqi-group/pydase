from typing import Any

from pytest import LogCaptureFixture

import pydase.units as u
from pydase.data_service.data_service import DataService


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

    service = ServiceClass()

    # You can just set floats to the Quantity objects. The DataService __setattr__ will
    # automatically convert this
    service.voltage = 10.0  # type: ignore
    service.current = 1.5

    assert service.voltage == 10.0 * u.units.V  # type: ignore
    assert service.current == 1.5 * u.units.mA

    assert "ServiceClass.voltage changed to 10.0 V" in caplog.text
    assert "ServiceClass.current changed to 1.5 mA" in caplog.text

    service.voltage = 12.0 * u.units.V  # type: ignore
    service.current = 1.51 * u.units.A
    assert service.voltage == 12.0 * u.units.V  # type: ignore
    assert service.current == 1.51 * u.units.A

    assert "ServiceClass.voltage changed to 12.0 V" in caplog.text
    assert "ServiceClass.current changed to 1.51 A" in caplog.text


def test_convert_to_quantity() -> None:
    assert u.convert_to_quantity(1.0, unit="V") == 1.0 * u.units.V
    assert u.convert_to_quantity(1, unit="mV") == 1.0 * u.units.mV
    assert u.convert_to_quantity({"magnitude": 12, "unit": "kV"}) == 12.0 * u.units.kV
    assert u.convert_to_quantity(1.0 * u.units.mV) == 1.0 * u.units.mV


def test_update_DataService_attribute(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        voltage = 1.0 * u.units.V
        _current: u.Quantity = 1.0 * u.units.mA

        @property
        def current(self) -> u.Quantity:
            return self._current

        @current.setter
        def current(self, value: Any) -> None:
            self._current = value

    service = ServiceClass()

    service.update_DataService_attribute(
        path_list=[], attr_name="voltage", value=1.0 * u.units.mV
    )

    assert "ServiceClass.voltage changed to 1.0 mV" in caplog.text

    service.update_DataService_attribute(path_list=[], attr_name="voltage", value=2)

    assert "ServiceClass.voltage changed to 2.0 mV" in caplog.text

    service.update_DataService_attribute(
        path_list=[], attr_name="voltage", value={"magnitude": 123, "unit": "kV"}
    )

    assert "ServiceClass.voltage changed to 123.0 kV" in caplog.text


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
        def __init__(self):
            self._unit: u.Quantity = 1 * u.units.A
            super().__init__()

        @property
        def some_unit(self) -> u.Quantity:
            return self._unit

        @some_unit.setter
        def some_unit(self, value: u.Quantity) -> None:
            assert isinstance(value, u.Quantity)
            self._unit = value

    service = ServiceClass()

    service.load_DataService_from_JSON(JSON_DICT)

    assert "ServiceClass.some_unit changed to 10.0 A" in caplog.text
