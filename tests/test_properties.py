from pytest import CaptureFixture

from pyDataInterface import DataService


def test_properties(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        _voltage = 10.0
        _current = 1.0

        @property
        def power(self) -> float:
            return self._voltage * self.current

        @property
        def voltage(self) -> float:
            return self._voltage

        @voltage.setter
        def voltage(self, value: float) -> None:
            self._voltage = value

        @property
        def current(self) -> float:
            return self._current

        @current.setter
        def current(self, value: float) -> None:
            self._current = value

    test_service = ServiceClass()
    test_service.voltage = 1

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.power = 1.0",
            "ServiceClass.voltage = 1.0",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    test_service.current = 12.0

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.power = 12.0",
            "ServiceClass.current = 12.0",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_nested_properties(capsys: CaptureFixture) -> None:
    class SubSubClass(DataService):
        name = "Hello"

    class SubClass(DataService):
        name = "Hello"
        class_attr = SubSubClass()

    class ServiceClass(DataService):
        class_attr = SubClass()
        name = "World"

        @property
        def subsub_name(self) -> str:
            return f"{self.class_attr.class_attr.name} {self.name}"

        @property
        def sub_name(self) -> str:
            return f"{self.class_attr.name} {self.name}"

    test_service = ServiceClass()
    test_service.name = "Peepz"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.name = Peepz",
            "ServiceClass.sub_name = Hello Peepz",
            "ServiceClass.subsub_name = Hello Peepz",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    test_service.class_attr.name = "Hi"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.sub_name = Hi Peepz",
            "ServiceClass.subsub_name = Hello Peepz",  # registers subclass changes
            "ServiceClass.class_attr.name = Hi",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    test_service.class_attr.class_attr.name = "Ciao"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.sub_name = Hi Peepz",  # registers subclass changes
            "ServiceClass.subsub_name = Ciao Peepz",
            "ServiceClass.class_attr.class_attr.name = Ciao",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_simple_list_properties(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        list = ["Hello", "Ciao"]
        name = "World"

        @property
        def total_name(self) -> str:
            return f"{self.list[0]} {self.name}"

    test_service = ServiceClass()
    test_service.name = "Peepz"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.name = Peepz",
            "ServiceClass.total_name = Hello Peepz",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    test_service.list[0] = "Hi"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.total_name = Hi Peepz",
            "ServiceClass.list[0] = Hi",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_class_list_properties(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    class ServiceClass(DataService):
        list = [SubClass()]
        name = "World"

        @property
        def total_name(self) -> str:
            return f"{self.list[0].name} {self.name}"

    test_service = ServiceClass()
    test_service.name = "Peepz"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.name = Peepz",
            "ServiceClass.total_name = Hello Peepz",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    test_service.list[0].name = "Hi"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.total_name = Hi Peepz",
            "ServiceClass.list[0].name = Hi",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_subclass_properties(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"
        _voltage = 10.0
        _current = 1.0

        @property
        def power(self) -> float:
            return self._voltage * self.current

        @property
        def voltage(self) -> float:
            return self._voltage

        @voltage.setter
        def voltage(self, value: float) -> None:
            self._voltage = value

        @property
        def current(self) -> float:
            return self._current

        @current.setter
        def current(self, value: float) -> None:
            self._current = value

    class ServiceClass(DataService):
        class_attr = SubClass()

    test_service = ServiceClass()
    test_service.class_attr.voltage = 10.0

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.class_attr.voltage = 10.0",
            "ServiceClass.class_attr.power = 10.0",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_subclass_properties(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"
        _voltage = 10.0
        _current = 1.0

        @property
        def power(self) -> float:
            return self._voltage * self.current

        @property
        def voltage(self) -> float:
            return self._voltage

        @voltage.setter
        def voltage(self, value: float) -> None:
            self._voltage = value

        @property
        def current(self) -> float:
            return self._current

        @current.setter
        def current(self, value: float) -> None:
            self._current = value

    class ServiceClass(DataService):
        class_attr = SubClass()

        @property
        def voltage(self) -> float:
            return self.class_attr.voltage

    test_service = ServiceClass()
    test_service.class_attr.voltage = 10.0

    captured = capsys.readouterr()
    expected_output = sorted(
        {
            "ServiceClass.class_attr.voltage = 10.0",
            "ServiceClass.class_attr.power = 10.0",
            "ServiceClass.voltage = 10.0",
        }
    )
    # using a set here as "ServiceClass.voltage = 10.0" is emitted twice. Once for
    # changing voltage, and once for changing power.
    actual_output = sorted(set(captured.out.strip().split("\n")))
    assert actual_output == expected_output


def test_subclass_properties_2(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"
        _voltage = 10.0
        _current = 1.0

        @property
        def power(self) -> float:
            return self._voltage * self.current

        @property
        def voltage(self) -> float:
            return self._voltage

        @voltage.setter
        def voltage(self, value: float) -> None:
            self._voltage = value

        @property
        def current(self) -> float:
            return self._current

        @current.setter
        def current(self, value: float) -> None:
            self._current = value

    class ServiceClass(DataService):
        class_attr = [SubClass() for i in range(2)]

        @property
        def voltage(self) -> float:
            return self.class_attr[0].voltage

    test_service = ServiceClass()
    test_service.class_attr[1].current = 10.0

    captured = capsys.readouterr()
    expected_output = sorted(
        {
            "ServiceClass.class_attr[1].current = 10.0",
            "ServiceClass.class_attr[1].power = 100.0",
            "ServiceClass.voltage = 10.0",
        }
    )
    # using a set here as "ServiceClass.voltage = 10.0" is emitted twice. Once for
    # changing current, and once for changing power. Note that the voltage property is
    # only dependent on class_attr[0] but still emits an update notification. This is
    # because every time any item in the list `test_service.class_attr` is changed,
    # a notification will be emitted.
    actual_output = sorted(set(captured.out.strip().split("\n")))
    assert actual_output == expected_output


def test_subsubclass_properties(capsys: CaptureFixture) -> None:
    class SubSubClass(DataService):
        _voltage = 10.0

        @property
        def voltage(self) -> float:
            return self._voltage

        @voltage.setter
        def voltage(self, value: float) -> None:
            self._voltage = value

    class SubClass(DataService):
        class_attr = SubSubClass()
        current = 0.5

        @property
        def power(self) -> float:
            return self.class_attr.voltage * self.current

    class ServiceClass(DataService):
        class_attr = [SubClass() for i in range(2)]

        @property
        def power(self) -> float:
            return self.class_attr[0].power

    test_service = ServiceClass()

    test_service.class_attr[1].class_attr.voltage = 100.0
    captured = capsys.readouterr()
    expected_output = sorted(
        {
            "ServiceClass.class_attr[0].class_attr.voltage = 100.0",
            "ServiceClass.class_attr[1].class_attr.voltage = 100.0",
            "ServiceClass.class_attr[0].power = 50.0",
            "ServiceClass.class_attr[1].power = 50.0",
            "ServiceClass.power = 50.0",
        }
    )
    actual_output = sorted(set(captured.out.strip().split("\n")))
    assert actual_output == expected_output


def test_subsubclass_instance_properties(capsys: CaptureFixture) -> None:
    class SubSubClass(DataService):
        def __init__(self) -> None:
            self._voltage = 10.0
            super().__init__()

        @property
        def voltage(self) -> float:
            return self._voltage

        @voltage.setter
        def voltage(self, value: float) -> None:
            self._voltage = value

    class SubClass(DataService):
        def __init__(self) -> None:
            self.attr = [SubSubClass()]
            self.current = 0.5
            super().__init__()

        @property
        def power(self) -> float:
            return self.attr[0].voltage * self.current

    class ServiceClass(DataService):
        class_attr = [SubClass() for i in range(2)]

        @property
        def power(self) -> float:
            return self.class_attr[0].power

    test_service = ServiceClass()

    test_service.class_attr[1].attr[0].voltage = 100.0
    captured = capsys.readouterr()
    # again, changing an item in a list will trigger the callbacks. This is why a
    # notification for `ServiceClass.power` is emitted although it did not change its
    # value
    expected_output = sorted(
        {
            "ServiceClass.class_attr[1].attr[0].voltage = 100.0",
            "ServiceClass.class_attr[1].power = 50.0",
            "ServiceClass.power = 5.0",
        }
    )
    actual_output = sorted(set(captured.out.strip().split("\n")))
    assert actual_output == expected_output
