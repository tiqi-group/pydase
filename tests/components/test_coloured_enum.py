from pytest import LogCaptureFixture

from pydase.components.coloured_enum import ColouredEnum
from pydase.data_service.data_service import DataService


def test_ColouredEnum(caplog: LogCaptureFixture) -> None:
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

    assert "ServiceClass.status changed to MyStatus.FAILING" in caplog.text


def test_warning(caplog: LogCaptureFixture) -> None:  # noqa
    class MyStatus(ColouredEnum):
        RUNNING = "#00FF00"
        FAILING = "#FF0000"

    class ServiceClass(DataService):
        status = MyStatus.RUNNING

    assert (
        "Warning: Class MyStatus does not inherit from DataService." not in caplog.text
    )
