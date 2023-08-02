from pytest import CaptureFixture

from pyDataInterface import DataService


def test_properties(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        _power = True

        @property
        def power(self) -> bool:
            return self._power

        @power.setter
        def power(self, value: bool) -> None:
            self._power = value

        @property
        def power_two(self) -> bool:
            return self._power

    test_service = ServiceClass()
    test_service.power = False

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.power = False",
            "ServiceClass.power_two = False",
            "ServiceClass._power = False",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output
