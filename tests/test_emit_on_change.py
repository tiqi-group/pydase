from typing import Any

from pytest import CaptureFixture

from pyDataInterface import DataService


def emit(self: Any, access_path: set[str], name: str, value: Any) -> None:
    if isinstance(value, DataService):
        value = value.serialize()

    for path in access_path:
        print(f"{path}.{name} = {value}")


DataService._emit = emit  # type: ignore


def test_class_attribute(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        attr = 0

    service_instance = ServiceClass()

    service_instance.attr = 1
    captured = capsys.readouterr()
    assert captured.out == "ServiceClass.attr = 1\n"


def test_instance_attribute(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = "Hello World"
            super().__init__()

    service_instance = ServiceClass()

    service_instance.attr = "Hello"
    captured = capsys.readouterr()
    assert captured.out == "ServiceClass.attr = Hello\n"


def test_class_list_attribute(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        attr = [0, 1]

    service_instance = ServiceClass()

    service_instance.attr[0] = 1337
    captured = capsys.readouterr()
    assert captured.out == "ServiceClass.attr[0] = 1337\n"


def test_instance_list_attribute(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "SubClass"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = [0, SubClass()]
            super().__init__()

    service_instance = ServiceClass()

    _ = capsys.readouterr()

    service_instance.attr[0] = "Hello"
    captured = capsys.readouterr()
    assert captured.out == "ServiceClass.attr[0] = Hello\n"

    service_instance.attr[1] = SubClass()
    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == "ServiceClass.attr[1] = {'name': {'type': 'str', 'value': 'SubClass',"
        " 'readonly': False}}"
    )


def test_reused_instance_list_attribute(capsys: CaptureFixture) -> None:
    some_list = [0, 1, 2]

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = some_list
            self.attr_2 = some_list
            self.attr_3 = [0, 1, 2]
            super().__init__()

    service_instance = ServiceClass()

    service_instance.attr[0] = "Hello"
    captured = capsys.readouterr()

    assert service_instance.attr == service_instance.attr_2
    assert service_instance.attr != service_instance.attr_3
    expected_output = sorted(
        [
            "ServiceClass.attr[0] = Hello",
            "ServiceClass.attr_2[0] = Hello",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_nested_reused_instance_list_attribute(capsys: CaptureFixture) -> None:
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

    _ = capsys.readouterr()
    service_instance.attr[0] = "Hello"
    captured = capsys.readouterr()

    assert service_instance.attr == service_instance.subclass.attr_list
    expected_output = sorted(
        [
            "ServiceClass.subclass.attr_list_2[0] = Hello",
            "ServiceClass.subclass.attr_list[0] = Hello",
            "ServiceClass.attr[0] = Hello",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output
