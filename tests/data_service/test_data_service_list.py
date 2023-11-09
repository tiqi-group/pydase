from typing import Any

from pytest import LogCaptureFixture

from pydase import DataService


def test_class_list_attribute(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        attr = [0, 1]

    service_instance = ServiceClass()

    service_instance.attr[0] = 1337
    assert "ServiceClass.attr[0] changed to 1337" in caplog.text
    caplog.clear()


def test_instance_list_attribute(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        name = "SubClass"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr: list[Any] = [0, SubClass()]
            super().__init__()

    service_instance = ServiceClass()

    service_instance.attr[0] = "Hello"
    assert "ServiceClass.attr[0] changed to Hello" in caplog.text
    caplog.clear()

    service_instance.attr[1] = SubClass()
    assert f"ServiceClass.attr[1] changed to {service_instance.attr[1]}" in caplog.text
    caplog.clear()


def test_reused_instance_list_attribute(caplog: LogCaptureFixture) -> None:
    some_list = [0, 1, 2]

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = some_list
            self.attr_2 = some_list
            self.attr_3 = [0, 1, 2]
            super().__init__()

    service_instance = ServiceClass()

    service_instance.attr[0] = 20
    assert service_instance.attr == service_instance.attr_2
    assert service_instance.attr != service_instance.attr_3

    assert "ServiceClass.attr[0] changed to 20" in caplog.text
    assert "ServiceClass.attr_2[0] changed to 20" in caplog.text


def test_nested_reused_instance_list_attribute(caplog: LogCaptureFixture) -> None:
    some_list = [0, 1, 2]

    class SubClass(DataService):
        attr_list = some_list

        def __init__(self) -> None:
            self.attr_list_2 = some_list
            super().__init__()

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = some_list
            self.subclass = SubClass()
            super().__init__()

    service_instance = ServiceClass()

    service_instance.attr[0] = 20

    assert service_instance.attr == service_instance.subclass.attr_list

    assert "ServiceClass.attr[0] changed to 20" in caplog.text
    assert "ServiceClass.subclass.attr_list[0] changed to 20" in caplog.text
    assert "ServiceClass.subclass.attr_list_2[0] changed to 20" in caplog.text


def test_protected_list_attribute(caplog: LogCaptureFixture) -> None:
    """Changing protected lists should not emit notifications for the lists themselves, but
    still for all properties depending on them.
    """

    class ServiceClass(DataService):
        _attr = [0, 1]

        @property
        def list_dependend_property(self) -> int:
            return self._attr[0]

    service_instance = ServiceClass()

    service_instance._attr[0] = 1337
    assert "ServiceClass.list_dependend_property changed to 1337" in caplog.text
