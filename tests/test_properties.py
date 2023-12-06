from pydase import DataService
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pytest import LogCaptureFixture


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

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.voltage = 1.0

    assert "'power' changed to '1.0'" in caplog.text
    assert "'voltage' changed to '1.0'" in caplog.text
    caplog.clear()

    service_instance.current = 12.0

    assert "'power' changed to '12.0'" in caplog.text
    assert "'current' changed to '12.0'" in caplog.text


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

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.name = "Peepz"

    assert "'name' changed to 'Peepz'" in caplog.text
    assert "'sub_name' changed to 'Hello Peepz'" in caplog.text
    assert "'subsub_name' changed to 'Hello Peepz'" in caplog.text
    caplog.clear()

    service_instance.class_attr.name = "Hi"
    assert service_instance.subsub_name == "Hello Peepz"

    assert "'sub_name' changed to 'Hi Peepz'" in caplog.text
    assert "'subsub_name' " not in caplog.text  # subsub_name does not depend on change
    assert "'class_attr.name' changed to 'Hi'" in caplog.text
    caplog.clear()

    service_instance.class_attr.class_attr.name = "Ciao"

    assert (
        "'sub_name' changed to" not in caplog.text
    )  # sub_name does not depend on change
    assert "'subsub_name' changed to 'Ciao Peepz'" in caplog.text
    assert "'class_attr.class_attr.name' changed to 'Ciao'" in caplog.text
    caplog.clear()


def test_simple_list_properties(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        list = ["Hello", "Ciao"]
        name = "World"

        @property
        def total_name(self) -> str:
            return f"{self.list[0]} {self.name}"

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.name = "Peepz"

    assert "'name' changed to 'Peepz'" in caplog.text
    assert "'total_name' changed to 'Hello Peepz'" in caplog.text
    caplog.clear()

    service_instance.list[0] = "Hi"

    assert "'total_name' changed to 'Hi Peepz'" in caplog.text
    assert "'list[0]' changed to 'Hi'" in caplog.text


def test_class_list_properties(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    class ServiceClass(DataService):
        list = [SubClass()]
        name = "World"

        @property
        def total_name(self) -> str:
            return f"{self.list[0].name} {self.name}"

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.name = "Peepz"

    assert "'name' changed to 'Peepz'" in caplog.text
    assert "'total_name' changed to 'Hello Peepz'" in caplog.text
    caplog.clear()

    service_instance.list[0].name = "Hi"

    assert "'total_name' changed to 'Hi Peepz'" in caplog.text
    assert "'list[0].name' changed to 'Hi'" in caplog.text


def test_subclass_properties(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"
        _voltage = 11.0
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

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.class_attr.voltage = 10.0

    assert "'class_attr.voltage' changed to '10.0'" in caplog.text
    assert "'class_attr.power' changed to '10.0'" in caplog.text
    assert "'voltage' changed to '10.0'" in caplog.text
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

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.class_attr[0].current = 10.0

    assert "'class_attr[0].current' changed to '10.0'" in caplog.text
    assert "'class_attr[0].power' changed to '100.0'" in caplog.text
    caplog.clear()

    service_instance.class_attr[0].voltage = 11.0
    assert "'class_attr[0].voltage' changed to '11.0'" in caplog.text
    assert "'class_attr[0].power' changed to '110.0'" in caplog.text
    assert "'voltage' changed to '11.0'" in caplog.text


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

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.class_attr[1].class_attr.voltage = 100.0
    assert "'class_attr[0].class_attr.voltage' changed to '100.0'" in caplog.text
    assert "'class_attr[1].class_attr.voltage' changed to '100.0'" in caplog.text
    assert "'class_attr[0].power' changed to '50.0'" in caplog.text
    assert "'class_attr[1].power' changed to '50.0'" in caplog.text
    assert "'power' changed to '50.0'" in caplog.text


def test_subsubclass_instance_properties(caplog: LogCaptureFixture) -> None:
    class SubSubClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self._voltage = 10.0

        @property
        def voltage(self) -> float:
            return self._voltage

        @voltage.setter
        def voltage(self, value: float) -> None:
            self._voltage = value

    class SubClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self.attr = [SubSubClass()]
            self.current = 0.5

        @property
        def power(self) -> float:
            return self.attr[0].voltage * self.current

    class ServiceClass(DataService):
        class_attr = [SubClass() for i in range(2)]

        @property
        def power(self) -> float:
            return self.class_attr[0].power

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.class_attr[0].attr[0].voltage = 100.0
    assert "'class_attr[0].attr[0].voltage' changed to '100.0'" in caplog.text
    assert "'class_attr[0].power' changed to '50.0'" in caplog.text
    assert "'power' changed to '50.0'" in caplog.text
