from typing import Any

import pytest
from pydase.observer_pattern.observable import Observable
from pydase.observer_pattern.observer import Observer


def test_abstract_method_error() -> None:
    class MyObserver(Observer):
        pass

    class MyObservable(Observable):
        pass

    with pytest.raises(TypeError):
        MyObserver(MyObservable())


def test_constructor_error() -> None:
    class MyObserver(Observer):
        def on_change(self, full_access_path: str, value: Any) -> None:
            pass

    with pytest.raises(TypeError):
        MyObserver()
