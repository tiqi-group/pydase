from pydase import DataService
from pytest import LogCaptureFixture


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


def test_protected_attribute_warning(caplog: LogCaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self._subclass = SubClass

    ServiceClass()

    assert (
        "Warning: Class SubClass does not inherit from DataService." not in caplog.text
    )
