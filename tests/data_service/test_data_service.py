from enum import Enum

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


def test_basic_inheritance_warning(caplog: LogCaptureFixture) -> None:
    class SubService(DataService):
        ...

    class SomeEnum(Enum):
        HI = 0

    class ServiceClass(DataService):
        sub_service = SubService()
        some_int = 1
        some_float = 1.0
        some_bool = True
        some_quantity = 1.0 * u.units.A
        some_string = "Hello"
        some_enum = SomeEnum.HI
        _name = "Service"

        @property
        def name(self) -> str:
            return self._name

        def some_method(self) -> None:
            ...

    ServiceClass()

    # neither of the attributes, methods or properties cause a warning log
    assert "WARNING" not in caplog.text


def test_class_attr_inheritance_warning(caplog: LogCaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        attr_1 = SubClass()

    ServiceClass()

    assert (
        "Class 'SubClass' does not inherit from DataService. This may lead to "
        "unexpected behaviour!"
    ) in caplog.text


def test_instance_attr_inheritance_warning(caplog: LogCaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self.attr_1 = SubClass()

    ServiceClass()

    assert (
        "Class 'SubClass' does not inherit from DataService. This may lead to "
        "unexpected behaviour!"
    ) in caplog.text


def test_protected_and_private_attribute_warning(caplog: LogCaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self._subclass = SubClass()
            self.__other_subclass = SubClass()

    ServiceClass()

    # Protected and private attributes are not checked
    assert (
        "Class 'SubClass' does not inherit from DataService. This may lead to "
        "unexpected behaviour!"
    ) not in caplog.text
