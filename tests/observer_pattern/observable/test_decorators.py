import pydase
import pytest
from pydase.observer_pattern.observable.decorators import validate_set


def test_validate_set_precision(caplog: pytest.LogCaptureFixture) -> None:
    class Service(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._value_1 = 0.0
            self._value_2 = 0.0

        @property
        def value_1(self) -> float:
            return self._value_1

        @value_1.setter
        @validate_set(precision=None)
        def value_1(self, value: float) -> None:
            self._value_1 = round(value, 1)

        @property
        def value_2(self) -> float:
            return self._value_2

        @value_2.setter
        @validate_set(precision=1e-1)
        def value_2(self, value: float) -> None:
            self._value_2 = round(value, 1)

    service_instance = Service()
    pydase.Server(service_instance)  # needed to initialise observer

    with pytest.raises(ValueError) as exc_info:
        service_instance.value_1 = 1.12
        assert "Failed to set value to 1.12 within 1 second. Current value: 1.1" in str(
            exc_info
        )

    caplog.clear()

    service_instance.value_2 = 1.12  # no assertion raised
    assert service_instance.value_2 == 1.1  # noqa

    assert "'value_2' changed to '1.1'" in caplog.text
