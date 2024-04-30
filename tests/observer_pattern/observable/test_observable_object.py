import logging
from typing import Any

import pytest
from pydase.observer_pattern.observable import Observable
from pydase.observer_pattern.observer import Observer

logger = logging.getLogger(__name__)


class MyObserver(Observer):
    def on_change(self, full_access_path: str, value: Any) -> None:
        logger.info("'%s' changed to '%s'", full_access_path, value)


def test_simple_instance_list_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.list_attr = [1, 2]

    instance = MyObservable()
    MyObserver(instance)
    instance.list_attr[0] = 12

    assert "'list_attr[0]' changed to '12'" in caplog.text


def test_instance_object_list_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Hello"

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.list_attr = [NestedObservable()]

    instance = MyObservable()
    MyObserver(instance)
    instance.list_attr[0].name = "Ciao"

    assert "'list_attr[0].name' changed to 'Ciao'" in caplog.text


def test_simple_class_list_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        list_attr = [1, 2]

    instance = MyObservable()
    MyObserver(instance)
    instance.list_attr[0] = 12

    assert "'list_attr[0]' changed to '12'" in caplog.text


def test_class_object_list_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        name = "Hello"

    class MyObservable(Observable):
        list_attr = [NestedObservable()]

    instance = MyObservable()
    MyObserver(instance)
    instance.list_attr[0].name = "Ciao"

    assert "'list_attr[0].name' changed to 'Ciao'" in caplog.text


def test_removed_observer_on_class_list_attr(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        name = "Hello"

    nested_instance = NestedObservable()

    class MyObservable(Observable):
        nested_attr = nested_instance
        changed_list_attr = [nested_instance]

    instance = MyObservable()
    MyObserver(instance)
    instance.changed_list_attr[0] = "Ciao"

    assert "'changed_list_attr[0]' changed to 'Ciao'" in caplog.text
    caplog.clear()

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_list_attr[0].name' changed to 'Hi'" not in caplog.text


def test_removed_observer_on_instance_list_attr(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class NestedObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Hello"

    nested_instance = NestedObservable()

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.nested_attr = nested_instance
            self.changed_list_attr = [nested_instance]

    instance = MyObservable()
    MyObserver(instance)
    instance.changed_list_attr[0] = "Ciao"

    assert "'changed_list_attr[0]' changed to 'Ciao'" in caplog.text
    caplog.clear()

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_list_attr[0].name' changed to 'Hi'" not in caplog.text


def test_list_append(caplog: pytest.LogCaptureFixture) -> None:
    class OtherObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.greeting = "Other Observable"

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.my_list = []

    observable_instance = MyObservable()
    MyObserver(observable_instance)

    observable_instance.my_list.append(OtherObservable())
    assert f"'my_list' changed to '{observable_instance.my_list}'" in caplog.text
    caplog.clear()

    observable_instance.my_list.append(OtherObservable())
    assert f"'my_list' changed to '{observable_instance.my_list}'" in caplog.text
    caplog.clear()

    observable_instance.my_list[0].greeting = "Hi"
    observable_instance.my_list[1].greeting = "Hello"

    assert observable_instance.my_list[0].greeting == "Hi"
    assert observable_instance.my_list[1].greeting == "Hello"
    assert "'my_list[0].greeting' changed to 'Hi'" in caplog.text
    assert "'my_list[1].greeting' changed to 'Hello'" in caplog.text


def test_list_pop(caplog: pytest.LogCaptureFixture) -> None:
    class OtherObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.greeting = "Hello there!"

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.my_list = [OtherObservable() for _ in range(2)]

    observable_instance = MyObservable()
    MyObserver(observable_instance)

    popped_instance = observable_instance.my_list.pop(0)

    assert len(observable_instance.my_list) == 1
    assert f"'my_list' changed to '{observable_instance.my_list}'" in caplog.text

    # checks if observer is removed
    popped_instance.greeting = "Ciao"
    assert "'my_list[0].greeting' changed to 'Ciao'" not in caplog.text
    caplog.clear()

    # checks if observer keys have been updated (index 1 moved to 0)
    observable_instance.my_list[0].greeting = "Hi"
    assert "'my_list[0].greeting' changed to 'Hi'" in caplog.text


def test_list_clear(caplog: pytest.LogCaptureFixture) -> None:
    class OtherObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.greeting = "Hello there!"

    other_observable_instance = OtherObservable()

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.my_list = [other_observable_instance]

    observable_instance = MyObservable()
    MyObserver(observable_instance)

    other_observable_instance.greeting = "Hello"
    assert "'my_list[0].greeting' changed to 'Hello'" in caplog.text

    observable_instance.my_list.clear()

    assert len(observable_instance.my_list) == 0
    assert "'my_list' changed to '[]'" in caplog.text

    # checks if observer has been removed
    other_observable_instance.greeting = "Hi"
    assert "'my_list[0].greeting' changed to 'Hi'" not in caplog.text


def test_list_extend(caplog: pytest.LogCaptureFixture) -> None:
    class OtherObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.greeting = "Hello there!"

    other_observable_instance = OtherObservable()

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.my_list = []

    observable_instance = MyObservable()
    MyObserver(observable_instance)

    other_observable_instance.greeting = "Hello"
    assert "'my_list[0].greeting' changed to 'Hello'" not in caplog.text

    observable_instance.my_list.extend([other_observable_instance, OtherObservable()])

    assert len(observable_instance.my_list) == 2
    assert f"'my_list' changed to '{observable_instance.my_list}'" in caplog.text

    # checks if observer has been removed
    other_observable_instance.greeting = "Hi"
    assert "'my_list[0].greeting' changed to 'Hi'" in caplog.text
    observable_instance.my_list[1].greeting = "Ciao"
    assert "'my_list[1].greeting' changed to 'Ciao'" in caplog.text


def test_list_insert(caplog: pytest.LogCaptureFixture) -> None:
    class OtherObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.greeting = "Hello there!"

    other_observable_instance_1 = OtherObservable()
    other_observable_instance_2 = OtherObservable()

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.my_list = [other_observable_instance_1, OtherObservable()]

    observable_instance = MyObservable()
    MyObserver(observable_instance)

    other_observable_instance_1.greeting = "Hello"
    assert "'my_list[0].greeting' changed to 'Hello'" in caplog.text

    observable_instance.my_list.insert(0, other_observable_instance_2)

    assert len(observable_instance.my_list) == 3
    assert f"'my_list' changed to '{observable_instance.my_list}'" in caplog.text

    # checks if observer keys have been updated
    other_observable_instance_2.greeting = "Hey"
    other_observable_instance_1.greeting = "Hi"
    observable_instance.my_list[2].greeting = "Ciao"

    assert "'my_list[0].greeting' changed to 'Hey'" in caplog.text
    assert "'my_list[1].greeting' changed to 'Hi'" in caplog.text
    assert "'my_list[2].greeting' changed to 'Ciao'" in caplog.text


def test_list_remove(caplog: pytest.LogCaptureFixture) -> None:
    class OtherObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.greeting = "Hello there!"

    other_observable_instance_1 = OtherObservable()
    other_observable_instance_2 = OtherObservable()

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.my_list = [other_observable_instance_1, other_observable_instance_2]

    observable_instance = MyObservable()
    MyObserver(observable_instance)

    other_observable_instance_1.greeting = "Hello"
    other_observable_instance_2.greeting = "Hi"
    caplog.clear()

    observable_instance.my_list.remove(other_observable_instance_1)

    assert len(observable_instance.my_list) == 1
    assert f"'my_list' changed to '{observable_instance.my_list}'" in caplog.text
    caplog.clear()

    # checks if observer has been removed
    other_observable_instance_1.greeting = "Hi"
    assert "'my_list[0].greeting' changed to 'Hi'" not in caplog.text
    caplog.clear()

    # checks if observer key was updated correctly (was index 1)
    other_observable_instance_2.greeting = "Ciao"
    assert "'my_list[0].greeting' changed to 'Ciao'" in caplog.text
