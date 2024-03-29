import logging

import pydase
import pytest
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager

logger = logging.getLogger()


def test_static_property_dependencies() -> None:
    class SubClass(pydase.DataService):
        _name = "SubClass"

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        def name(self, value: str) -> None:
            self._name = value

    class ServiceClass(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.list_attr = [SubClass()]
            self._name = "ServiceClass"

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        def name(self, value: str) -> None:
            self._name = value

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    observer = DataServiceObserver(state_manager)
    logger.debug(observer.property_deps_dict)
    assert observer.property_deps_dict == {
        "list_attr[0]._name": ["list_attr[0].name"],
        "_name": ["name"],
    }


def test_dynamic_list_property_dependencies() -> None:
    class SubClass(pydase.DataService):
        _name = "SubClass"

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        def name(self, value: str) -> None:
            self._name = value

    class ServiceClass(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.list_attr = [SubClass()]

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    observer = DataServiceObserver(state_manager)

    assert observer.property_deps_dict == {
        "list_attr[0]._name": ["list_attr[0].name"],
    }

    service_instance.list_attr.append(SubClass())

    assert observer.property_deps_dict == {
        "list_attr[0]._name": ["list_attr[0].name"],
        "list_attr[1]._name": ["list_attr[1].name"],
    }


def test_protected_or_private_change_logs(caplog: pytest.LogCaptureFixture) -> None:
    class OtherService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._name = "Hi"

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.subclass = OtherService()

    service = MyService()
    state_manager = StateManager(service)
    DataServiceObserver(state_manager)

    service.subclass._name = "Hello"
    assert "'subclass._name' changed to 'Hello'" not in caplog.text


def test_dynamic_list_entry_with_property(caplog: pytest.LogCaptureFixture) -> None:
    class PropertyClass(pydase.DataService):
        _name = "Hello"

        @property
        def name(self) -> str:
            """The name property."""
            return self._name

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.list_attr = []

        def toggle_high_voltage(self) -> None:
            self.list_attr = []
            self.list_attr.append(PropertyClass())
            self.list_attr[0]._name = "Hoooo"

    service = MyService()
    state_manager = StateManager(service)
    DataServiceObserver(state_manager)
    service.toggle_high_voltage()

    assert "'list_attr[0].name' changed to 'Hello'" not in caplog.text
    assert "'list_attr[0].name' changed to 'Hoooo'" in caplog.text
