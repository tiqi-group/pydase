from pydase import DataService
from pytest import LogCaptureFixture


def test_setattr_warnings(caplog: LogCaptureFixture) -> None:
    # def test_setattr_warnings(capsys: CaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self.attr_1 = SubClass()

    ServiceClass()

    assert "Warning: Class 'SubClass' does not inherit from DataService." in caplog.text


def test_private_attribute_warning(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self.__something = ""

    ServiceClass()

    assert (
        " Warning: You should not set private but rather protected attributes! Use "
        "_something instead of __something." in caplog.text
    )


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
