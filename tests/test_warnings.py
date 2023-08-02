from pytest import LogCaptureFixture

from pydase import DataService

from . import caplog  # noqa


def test_setattr_warnings(caplog: LogCaptureFixture) -> None:  # noqa
    # def test_setattr_warnings(capsys: CaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr_1 = SubClass()
            super().__init__()

    ServiceClass()

    assert "Warning: Class SubClass does not inherit from DataService." in caplog.text


def test_private_attribute_warning(caplog: LogCaptureFixture) -> None:  # noqa
    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.__something = ""
            super().__init__()

    ServiceClass()

    assert (
        " Warning: You should not set private but rather protected attributes! Use "
        "_something instead of __something." in caplog.text
    )
