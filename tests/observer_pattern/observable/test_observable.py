import logging
from typing import Any

import pytest
from pydase.observer_pattern.observable import Observable
from pydase.observer_pattern.observer import Observer

logger = logging.getLogger("pydase")
logger.propagate = True


class MyObserver(Observer):
    def on_change(self, full_access_path: str, value: Any) -> None:
        logger.info("'%s' changed to '%s'", full_access_path, value)


def test_constructor_error_message(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        def __init__(self) -> None:
            self.attr = 1
            super().__init__()

    MyObservable()

    assert (
        "Ensure that super().__init__() is called at the start of the 'MyObservable' "
        "constructor! Failing to do so may lead to unexpected behavior." in caplog.text
    )


def test_simple_class_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        int_attribute = 10

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.int_attribute = 12

    assert "'int_attribute' changed to '12'" in caplog.text


def test_simple_instance_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.int_attribute = 10

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.int_attribute = 12

    assert "'int_attribute' changed to '12'" in caplog.text


def test_nested_class_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MySubclass(Observable):
        name = "My Subclass"

    class MyObservable(Observable):
        subclass = MySubclass()

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.subclass.name = "Other name"

    assert "'subclass.name' changed to 'Other name'" in caplog.text


def test_nested_instance_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MySubclass(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Subclass name"

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.subclass = MySubclass()

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.subclass.name = "Other name"

    assert "'subclass.name' changed to 'Other name'" in caplog.text


def test_removed_observer_on_class_attr(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        name = "Hello"

    nested_instance = NestedObservable()

    class MyObservable(Observable):
        nested_attr = nested_instance
        changed_attr = nested_instance

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.changed_attr = "Ciao"

    assert "'changed_attr' changed to 'Ciao'" in caplog.text
    caplog.clear()

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_attr.name' changed to 'Hi'" not in caplog.text


def test_removed_observer_on_instance_attr(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Hello"

    nested_instance = NestedObservable()

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.nested_attr = nested_instance
            self.changed_attr = nested_instance

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.changed_attr = "Ciao"

    assert "'changed_attr' changed to 'Ciao'" in caplog.text
    caplog.clear()

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_attr.name' changed to 'Hi'" not in caplog.text


def test_property_getter(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self._name = "Hello"

        @property
        def name(self) -> str:
            """The name property."""
            return self._name

    instance = MyObservable()
    observer = MyObserver(instance)
    _ = instance.name

    assert "'name' changed to 'Hello'" in caplog.text


def test_property_setter(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self._name = "Hello"

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        def name(self, value: str) -> None:
            self._name = value

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.name = "Ciao"

    assert "'name' changed to 'Hello'" not in caplog.text
    assert "'name' changed to 'Ciao'" in caplog.text
