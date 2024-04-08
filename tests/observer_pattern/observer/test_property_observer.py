from typing import Any

from pydase.observer_pattern.observable.observable import Observable
from pydase.observer_pattern.observer.property_observer import PropertyObserver


def test_inherited_property_dependency_resolution() -> None:
    class BaseObservable(Observable):
        _name = "BaseObservable"

        @property
        def name(self) -> str:
            return self._name

    class DerivedObservable(BaseObservable):
        _name = "DerivedObservable"

    class MyObserver(PropertyObserver):
        def on_change(self, full_access_path: str, value: Any) -> None: ...

    assert MyObserver(DerivedObservable()).property_deps_dict == {"_name": ["name"]}
