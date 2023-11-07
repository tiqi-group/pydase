from pytest import LogCaptureFixture

from pydase import DataService


def test_properties(caplog: LogCaptureFixture) -> None:
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

    assert "ServiceClass.power changed to 1.0" in caplog.text
    assert "ServiceClass.voltage changed to 1.0" in caplog.text
    caplog.clear()

    test_service.current = 12.0

    assert "ServiceClass.power changed to 12.0" in caplog.text
    assert "ServiceClass.current changed to 12.0" in caplog.text


def test_nested_properties(caplog: LogCaptureFixture) -> None:
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

    assert "ServiceClass.name changed to Peepz" in caplog.text
    assert "ServiceClass.sub_name changed to Hello Peepz" in caplog.text
    assert "ServiceClass.subsub_name changed to Hello Peepz" in caplog.text
    caplog.clear()

    test_service.class_attr.name = "Hi"

    assert "ServiceClass.sub_name changed to Hi Peepz" in caplog.text
    assert (
        "ServiceClass.subsub_name changed to Hello Peepz" in caplog.text
    )  # registers subclass changes
    assert "ServiceClass.class_attr.name changed to Hi" in caplog.text
    caplog.clear()

    test_service.class_attr.class_attr.name = "Ciao"

    assert (
        "ServiceClass.sub_name changed to Hi Peepz" in caplog.text
    )  # registers subclass changes
    assert "ServiceClass.subsub_name changed to Ciao Peepz" in caplog.text
    assert "ServiceClass.class_attr.class_attr.name changed to Ciao" in caplog.text
    caplog.clear()


def test_simple_list_properties(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        list = ["Hello", "Ciao"]
        name = "World"

        @property
        def total_name(self) -> str:
            return f"{self.list[0]} {self.name}"

    test_service = ServiceClass()
    test_service.name = "Peepz"

    assert "ServiceClass.name changed to Peepz" in caplog.text
    assert "ServiceClass.total_name changed to Hello Peepz" in caplog.text
    caplog.clear()

    test_service.list[0] = "Hi"

    assert "ServiceClass.total_name changed to Hi Peepz" in caplog.text
    assert "ServiceClass.list[0] changed to Hi" in caplog.text


def test_class_list_properties(caplog: LogCaptureFixture) -> None:
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

    assert "ServiceClass.name changed to Peepz" in caplog.text
    assert "ServiceClass.total_name changed to Hello Peepz" in caplog.text
    caplog.clear()

    test_service.list[0].name = "Hi"

    assert "ServiceClass.total_name changed to Hi Peepz" in caplog.text
    assert "ServiceClass.list[0].name changed to Hi" in caplog.text


def test_subclass_properties(caplog: LogCaptureFixture) -> None:
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

    # using a set here as "ServiceClass.voltage = 10.0" is emitted twice. Once for
    # changing voltage, and once for changing power.
    assert "ServiceClass.class_attr.voltage changed to 10.0" in caplog.text
    assert "ServiceClass.class_attr.power changed to 10.0" in caplog.text
    assert "ServiceClass.voltage changed to 10.0" in caplog.text
    caplog.clear()


def test_subclass_properties_2(caplog: LogCaptureFixture) -> None:
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

    # using a set here as "ServiceClass.voltage = 10.0" is emitted twice. Once for
    # changing current, and once for changing power. Note that the voltage property is
    # only dependent on class_attr[0] but still emits an update notification. This is
    # because every time any item in the list `test_service.class_attr` is changed,
    # a notification will be emitted.
    assert "ServiceClass.class_attr[1].current changed to 10.0" in caplog.text
    assert "ServiceClass.class_attr[1].power changed to 100.0" in caplog.text
    assert "ServiceClass.voltage changed to 10.0" in caplog.text


def test_subsubclass_properties(caplog: LogCaptureFixture) -> None:
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
    assert (
        "ServiceClass.class_attr[0].class_attr.voltage changed to 100.0" in caplog.text
    )
    assert (
        "ServiceClass.class_attr[1].class_attr.voltage changed to 100.0" in caplog.text
    )
    assert "ServiceClass.class_attr[0].power changed to 50.0" in caplog.text
    assert "ServiceClass.class_attr[1].power changed to 50.0" in caplog.text
    assert "ServiceClass.power changed to 50.0" in caplog.text


def test_subsubclass_instance_properties(caplog: LogCaptureFixture) -> None:
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
    # again, changing an item in a list will trigger the callbacks. This is why a
    # notification for `ServiceClass.power` is emitted although it did not change its
    # value
    assert "ServiceClass.class_attr[1].attr[0].voltage changed to 100.0" in caplog.text
    assert "ServiceClass.class_attr[1].power changed to 50.0" in caplog.text
    assert "ServiceClass.power changed to 5.0" in caplog.text
