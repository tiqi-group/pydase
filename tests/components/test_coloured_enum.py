from pytest import CaptureFixture, LogCaptureFixture

from pydase.components.coloured_enum import ColouredEnum
from pydase.data_service.data_service import DataService

from .. import caplog  # noqa


def test_ColouredEnum(capsys: CaptureFixture) -> None:
    class MyStatus(ColouredEnum):
        RUNNING = "#00FF00"
        FAILING = "#FF0000"

    class ServiceClass(DataService):
        _status = MyStatus.RUNNING

        @property
        def status(self) -> MyStatus:
            return self._status

        @status.setter
        def status(self, value: MyStatus) -> None:
            # do something ...
            self._status = value

    service = ServiceClass()

    service.status = MyStatus.FAILING

    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.status = MyStatus.FAILING",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output


def test_warning(caplog: LogCaptureFixture) -> None:  # noqa
    class MyStatus(ColouredEnum):
        RUNNING = "#00FF00"
        FAILING = "#FF0000"

    class ServiceClass(DataService):
        status = MyStatus.RUNNING

    assert (
        "Warning: Class MyStatus does not inherit from DataService." not in caplog.text
    )
