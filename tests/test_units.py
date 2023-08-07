from typing import Any

from pytest import CaptureFixture

import pydase.units as u
from pydase.data_service.data_service import DataService


def test_DataService_setattr(capsys: CaptureFixture) -> None:
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
    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.voltage = 10.0 V",
            "ServiceClass.current = 1.5 mA",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output

    service.voltage = 12.0 * u.units.V  # type: ignore
    service.current = 1.51 * u.units.A
    assert service.voltage == 12.0 * u.units.V  # type: ignore
    assert service.current == 1.51 * u.units.A
    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.voltage = 12.0 V",
            "ServiceClass.current = 1.51 A",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output


def test_convert_to_quantity() -> None:
    assert u.convert_to_quantity(1.0, unit="V") == 1.0 * u.units.V
    assert u.convert_to_quantity(1, unit="mV") == 1.0 * u.units.mV
    assert u.convert_to_quantity({"magnitude": 12, "unit": "kV"}) == 12.0 * u.units.kV
    assert u.convert_to_quantity(1.0 * u.units.mV) == 1.0 * u.units.mV


def test_update_DataService_attribute(capsys: CaptureFixture) -> None:
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
    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.voltage = 1.0 mV",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output

    service.update_DataService_attribute(path_list=[], attr_name="voltage", value=2)
    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.voltage = 2.0 mV",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output

    service.update_DataService_attribute(
        path_list=[], attr_name="voltage", value={"magnitude": 123, "unit": "kV"}
    )
    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.voltage = 123.0 kV",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output
