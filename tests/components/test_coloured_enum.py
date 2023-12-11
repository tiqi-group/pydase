from pydase.components.coloured_enum import ColouredEnum
from pydase.data_service.data_service import DataService
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pytest import LogCaptureFixture


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

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.status = MyStatus.FAILING

    assert "'status' changed to 'MyStatus.FAILING'" in caplog.text


def test_warning(caplog: LogCaptureFixture) -> None:
    class MyStatus(ColouredEnum):
        RUNNING = "#00FF00"
        FAILING = "#FF0000"

    class ServiceClass(DataService):
        status = MyStatus.RUNNING

    ServiceClass()

    assert (
        "Class 'MyStatus' does not inherit from DataService. This may lead to "
        "unexpected behaviour!" not in caplog.text
    )
