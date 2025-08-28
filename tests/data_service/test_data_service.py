from enum import Enum
from typing import Any

import pytest
from pytest import LogCaptureFixture

import pydase
import pydase.units as u
from pydase import DataService
from pydase.utils.decorators import FunctionDefinitionError, frontend


def test_basic_inheritance_warning(caplog: LogCaptureFixture) -> None:
    class SubService(DataService): ...

    class SomeEnum(Enum):
        HI = 0

    class ServiceClass(DataService):
        sub_service = SubService()
        some_int = 1
        some_float = 1.0
        some_bool = True
        some_quantity = 1.0 * u.units.A
        some_list = [1, 2]
        some_string = "Hello"
        some_enum = SomeEnum.HI
        _name = "Service"

        @property
        def name(self) -> str:
            return self._name

        def some_method(self) -> None: ...

        async def some_task(self) -> None: ...

    ServiceClass()

    # neither of the attributes, methods or properties cause a warning log
    assert "WARNING" not in caplog.text


def test_class_attr_inheritance_warning(caplog: LogCaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        attr_1 = SubClass()

    ServiceClass()

    assert (
        "Class 'SubClass' does not inherit from DataService. This may lead to "
        "unexpected behaviour!"
    ) in caplog.text


def test_instance_attr_inheritance_warning(caplog: LogCaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self.attr_1 = SubClass()

    ServiceClass()

    assert (
        "Class 'SubClass' does not inherit from DataService. This may lead to "
        "unexpected behaviour!"
    ) in caplog.text


def test_protected_and_private_attribute_warning(caplog: LogCaptureFixture) -> None:
    class SubClass:
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            super().__init__()
            self._subclass = SubClass()
            self.__other_subclass = SubClass()

    ServiceClass()

    # Protected and private attributes are not checked
    assert (
        "Class 'SubClass' does not inherit from DataService. This may lead to "
        "unexpected behaviour!"
    ) not in caplog.text


def test_exposing_methods(caplog: LogCaptureFixture) -> None:
    with pytest.raises(FunctionDefinitionError):

        class ClassWithMethod(pydase.DataService):
            @frontend
            def some_method(self, *args: Any) -> str:
                return "some method"

    class ClassWithTask(pydase.DataService):
        @frontend
        def some_method(self) -> str:
            return "some method"

    ClassWithTask()


def test_dynamically_added_attribute(caplog: LogCaptureFixture) -> None:
    class MyService(DataService):
        pass

    service_instance = MyService()
    pydase.Server(service_instance)

    service_instance.dynamically_added_attr = 1.0

    assert ("'dynamically_added_attr' changed to '1.0'") in caplog.text
