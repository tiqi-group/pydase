import logging
from typing import Any

import pydase
import pytest
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.utils.serialization.serializer import SerializationError, dump

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


def test_private_attribute_does_not_have_to_be_serializable() -> None:
    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.publ_attr: Any = 1
            self.__priv_attr = (1,)

        def change_publ_attr(self) -> None:
            self.publ_attr = (2,)  # cannot be serialized

        def change_priv_attr(self) -> None:
            self.__priv_attr = (2,)

    service_instance = MyService()
    pydase.Server(service_instance)

    with pytest.raises(SerializationError):
        service_instance.change_publ_attr()

    service_instance.change_priv_attr()


def test_normalized_attr_path_in_dependent_property_changes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class SubService(pydase.DataService):
        _prop = 10.0

        @property
        def prop(self) -> float:
            return self._prop

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.service_dict = {"one": SubService()}

    service_instance = MyService()
    state_manager = StateManager(service=service_instance)
    observer = DataServiceObserver(state_manager=state_manager)

    assert observer.property_deps_dict['service_dict["one"]._prop'] == [
        'service_dict["one"].prop'
    ]

    # We can use dict key path encoded with double quotes
    state_manager.set_service_attribute_value_by_path(
        'service_dict["one"]._prop', dump(11.0)
    )
    assert service_instance.service_dict["one"].prop == 11.0
    assert "'service_dict[\"one\"].prop' changed to '11.0'" in caplog.text

    # We can use dict key path encoded with single quotes
    state_manager.set_service_attribute_value_by_path(
        "service_dict['one']._prop", dump(12.0)
    )
    assert service_instance.service_dict["one"].prop == 12.0
    assert "'service_dict[\"one\"].prop' changed to '12.0'" in caplog.text


def test_nested_dict_property_changes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def get_voltage() -> float:
        """Mocking a remote device."""
        return 2.0

    def set_voltage(value: float) -> None:
        """Mocking a remote device."""

    class OtherService(pydase.DataService):
        _voltage = 1.0

        @property
        def voltage(self) -> float:
            # Property dependency _voltage changes within the property itself.
            # This should be handled gracefully, i.e. not introduce recursion
            self._voltage = get_voltage()
            return self._voltage

        @voltage.setter
        def voltage(self, value: float) -> None:
            self._voltage = value
            set_voltage(self._voltage)

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.my_dict = {"key": OtherService()}

    service = MyService()
    pydase.Server(service)

    # Changing the _voltage attribute should re-evaluate the voltage property, but avoid
    # recursion
    service.my_dict["key"].voltage = 1.2
