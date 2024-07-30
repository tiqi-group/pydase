import logging
from typing import Any

import pytest
from pydase.observer_pattern.observable import Observable
from pydase.observer_pattern.observer import Observer

logger = logging.getLogger("pydase")


class MyObserver(Observer):
    def on_change(self, full_access_path: str, value: Any) -> None:
        logger.info("'%s' changed to '%s'", full_access_path, value)


def test_simple_class_dict_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        dict_attr = {"first": "Hello"}

    instance = MyObservable()
    MyObserver(instance)
    instance.dict_attr["first"] = "Ciao"
    instance.dict_attr["second"] = "World"

    assert "'dict_attr[\"first\"]' changed to 'Ciao'" in caplog.text
    assert "'dict_attr[\"second\"]' changed to 'World'" in caplog.text


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
    MyObserver(instance)
    instance.dict_attr["first"].name = "Ciao"

    assert "'dict_attr[\"first\"].name' changed to 'Ciao'" in caplog.text


def test_class_dict_attribute(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        name = "Hello"

    class MyObservable(Observable):
        dict_attr = {"first": NestedObservable()}

    instance = MyObservable()
    MyObserver(instance)
    instance.dict_attr["first"].name = "Ciao"

    assert "'dict_attr[\"first\"].name' changed to 'Ciao'" in caplog.text


def test_nested_dict_instances(caplog: pytest.LogCaptureFixture) -> None:
    dict_instance = {"first": "Hello", "second": "World"}

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.nested_dict_attr = {"nested": dict_instance}

    instance = MyObservable()
    MyObserver(instance)
    instance.nested_dict_attr["nested"]["first"] = "Ciao"

    assert "'nested_dict_attr[\"nested\"][\"first\"]' changed to 'Ciao'" in caplog.text


def test_dict_in_list_instance(caplog: pytest.LogCaptureFixture) -> None:
    dict_instance = {"first": "Hello", "second": "World"}

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.dict_in_list = [dict_instance]

    instance = MyObservable()
    MyObserver(instance)
    instance.dict_in_list[0]["first"] = "Ciao"

    assert "'dict_in_list[0][\"first\"]' changed to 'Ciao'" in caplog.text


def test_list_in_dict_instance(caplog: pytest.LogCaptureFixture) -> None:
    list_instance: list[Any] = [1, 2, 3]

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.list_in_dict = {"some_list": list_instance}

    instance = MyObservable()
    MyObserver(instance)
    instance.list_in_dict["some_list"][0] = "Ciao"

    assert "'list_in_dict[\"some_list\"][0]' changed to 'Ciao'" in caplog.text


def test_key_type_error(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.dict_attr = {1.0: 1.0}

    with pytest.raises(ValueError) as exc_info:
        MyObservable()

    assert (
        "Invalid key type: 1.0 (float). In pydase services, dictionary keys must be "
        "strings." in str(exc_info)
    )


def test_removed_observer_on_class_dict_attr(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Hello"

    nested_instance = NestedObservable()

    class MyObservable(Observable):
        nested_attr = nested_instance
        changed_dict_attr = {"nested": nested_instance}

    instance = MyObservable()
    MyObserver(instance)
    instance.changed_dict_attr["nested"] = "Ciao"

    assert "'changed_dict_attr[\"nested\"]' changed to 'Ciao'" in caplog.text
    caplog.clear()

    assert nested_instance._observers == {
        "nested_attr": [instance],
    }

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_dict_attr[\"nested\"].name' changed to 'Hi'" not in caplog.text


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
    MyObserver(instance)
    instance.changed_dict_attr["nested"] = "Ciao"

    assert "'changed_dict_attr[\"nested\"]' changed to 'Ciao'" in caplog.text
    caplog.clear()

    assert nested_instance._observers == {
        "nested_attr": [instance],
    }

    instance.nested_attr.name = "Hi"

    assert "'nested_attr.name' changed to 'Hi'" in caplog.text
    assert "'changed_dict_attr[\"nested\"].name' changed to 'Hi'" not in caplog.text


def test_dotted_dict_key(caplog: pytest.LogCaptureFixture) -> None:
    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.dict_attr = {"dotted.key": 1.0}

    instance = MyObservable()
    MyObserver(instance)
    instance.dict_attr["dotted.key"] = "Ciao"

    assert "'dict_attr[\"dotted.key\"]' changed to 'Ciao'" in caplog.text


def test_pop(caplog: pytest.LogCaptureFixture) -> None:
    class NestedObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.name = "Hello"

    nested_instance = NestedObservable()

    class MyObservable(Observable):
        def __init__(self) -> None:
            super().__init__()
            self.dict_attr = {"nested": nested_instance}

    instance = MyObservable()
    MyObserver(instance)
    assert instance.dict_attr.pop("nested") == nested_instance
    assert nested_instance._observers == {}

    assert f"'dict_attr' changed to '{instance.dict_attr}'" in caplog.text
