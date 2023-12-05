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
    observer = MyObserver(instance)
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
    observer = MyObserver(instance)
    instance.list_attr[0].name = "Ciao"

    assert "'list_attr[0].name' changed to 'Ciao'" in caplog.text


def test_simple_class_list_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        list_attr = [1, 2]

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.list_attr[0] = 12

    assert "'list_attr[0]' changed to '12'" in caplog.text


def test_class_object_list_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        name = "Hello"

    class MyObservable(Observable):
        list_attr = [NestedObservable()]

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.list_attr[0].name = "Ciao"

    assert "'list_attr[0].name' changed to 'Ciao'" in caplog.text


def test_simple_instance_dict_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.dict_attr = {"first": "Hello"}

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.dict_attr["first"] = "Ciao"
    instance.dict_attr["second"] = "World"

    assert "'dict_attr['first']' changed to 'Ciao'" in caplog.text
    assert "'dict_attr['second']' changed to 'World'" in caplog.text


def test_simple_class_dict_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        dict_attr = {"first": "Hello"}

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.dict_attr["first"] = "Ciao"
    instance.dict_attr["second"] = "World"

    assert "'dict_attr['first']' changed to 'Ciao'" in caplog.text
    assert "'dict_attr['second']' changed to 'World'" in caplog.text


def test_instance_dict_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Hello"

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.dict_attr = {"first": NestedObservable()}

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.dict_attr["first"].name = "Ciao"

    assert "'dict_attr['first'].name' changed to 'Ciao'" in caplog.text


def test_class_dict_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        name = "Hello"

    class MyObservable(Observable):
        dict_attr = {"first": NestedObservable()}

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.dict_attr["first"].name = "Ciao"

    assert "'dict_attr['first'].name' changed to 'Ciao'" in caplog.text


def test_removed_observer_on_class_list_attr(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        name = "Hello"

    nested_instance = NestedObservable()

    class MyObservable(Observable):
        nested_attr = nested_instance
        changed_list_attr = [nested_instance]

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.changed_list_attr[0] = "Ciao"

    assert "'changed_list_attr[0]' changed to 'Ciao'" in caplog.text
    caplog.clear()

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_list_attr[0].name' changed to 'Hi'" not in caplog.text


def test_removed_observer_on_instance_dict_attr(
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
            self.changed_dict_attr = {"nested": nested_instance}

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.changed_dict_attr["nested"] = "Ciao"

    assert "'changed_dict_attr['nested']' changed to 'Ciao'" in caplog.text
    caplog.clear()

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_dict_attr['nested'].name' changed to 'Hi'" not in caplog.text


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
    observer = MyObserver(instance)
    instance.changed_list_attr[0] = "Ciao"

    assert "'changed_list_attr[0]' changed to 'Ciao'" in caplog.text
    caplog.clear()

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_list_attr[0].name' changed to 'Hi'" not in caplog.text


def test_removed_observer_on_class_dict_attr(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Hello"

    nested_instance = NestedObservable()

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.nested_attr = nested_instance
            self.changed_dict_attr = {"nested": nested_instance}

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.changed_dict_attr["nested"] = "Ciao"

    assert "'changed_dict_attr['nested']' changed to 'Ciao'" in caplog.text
    caplog.clear()

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_dict_attr['nested'].name' changed to 'Hi'" not in caplog.text


def test_nested_dict_instances(caplog: pytest.LogCaptureFixture) -> None:
    dict_instance = {"first": "Hello", "second": "World"}

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.nested_dict_attr = {"nested": dict_instance}

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.nested_dict_attr["nested"]["first"] = "Ciao"

    assert "'nested_dict_attr['nested']['first']' changed to 'Ciao'" in caplog.text


def test_dict_in_list_instance(caplog: pytest.LogCaptureFixture) -> None:
    dict_instance = {"first": "Hello", "second": "World"}

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.dict_in_list = [dict_instance]

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.dict_in_list[0]["first"] = "Ciao"

    assert "'dict_in_list[0]['first']' changed to 'Ciao'" in caplog.text


def test_list_in_dict_instance(caplog: pytest.LogCaptureFixture) -> None:
    list_instance = [1, 2, 3]

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.list_in_dict = {"some_list": list_instance}

    instance = MyObservable()
    observer = MyObserver(instance)
    instance.list_in_dict["some_list"][0] = "Ciao"

    assert "'list_in_dict['some_list'][0]' changed to 'Ciao'" in caplog.text
