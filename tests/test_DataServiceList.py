from pytest import CaptureFixture

from pydase import DataService


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
        " 'readonly': False, 'doc': None}}"
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

    service_instance.attr[0] = 20
    captured = capsys.readouterr()

    assert service_instance.attr == service_instance.attr_2
    assert service_instance.attr != service_instance.attr_3
    expected_output = sorted(
        [
            "ServiceClass.attr[0] = 20",
            "ServiceClass.attr_2[0] = 20",
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
    service_instance.attr[0] = 20
    captured = capsys.readouterr()

    assert service_instance.attr == service_instance.subclass.attr_list
    expected_output = sorted(
        [
            "ServiceClass.subclass.attr_list_2[0] = 20",
            "ServiceClass.subclass.attr_list[0] = 20",
            "ServiceClass.attr[0] = 20",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_protected_list_attribute(capsys: CaptureFixture) -> None:
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
    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.list_dependend_property = 1337",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output
