import pydase.units as u
from pydase import DataService
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pytest import LogCaptureFixture


def test_unexpected_type_change_warning(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        attr_1 = 1.0
        current = 1.0 * u.units.A

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)
    service_instance.attr_1 = 2

    assert "'attr_1' changed to '2'" in caplog.text
    assert (
        "Type of 'attr_1' changed from 'float' to 'int'. This may have unwanted "
        "side effects! Consider setting it to 'float' directly." in caplog.text
    )

    service_instance.current = 2
    assert "'current' changed to '2'" in caplog.text
    assert (
        "Type of 'current' changed from 'Quantity' to 'int'. This may have unwanted "
        "side effects! Consider setting it to 'Quantity' directly." in caplog.text
    )
