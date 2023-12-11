import logging
from collections.abc import Callable

from pydase.components.number_slider import NumberSlider
from pydase.data_service.data_service import DataService
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pytest import LogCaptureFixture

from tests.utils.test_serializer import pytest

logger = logging.getLogger(__name__)


def test_number_slider(caplog: LogCaptureFixture) -> None:
    class MySlider(NumberSlider):
        def __init__(
            self,
            value: float = 0,
            min_: float = 0,
            max_: float = 100,
            step_size: float = 1,
            callback: Callable[..., None] = lambda: None,
        ) -> None:
            super().__init__(value, min_, max_, step_size)
            self._callback = callback

        @property
        def value(self) -> float:
            return self._value

        @value.setter
        def value(self, value: float) -> None:
            self._callback(value)
            self._value = value

        @property
        def min(self) -> float:
            return super().min

    class MyService(DataService):
        def __init__(self) -> None:
            super().__init__()
            self.my_slider = MySlider(callback=self.some_method)

        def some_method(self, slider_value: float) -> None:
            logger.info("Slider changed to '%s'", slider_value)

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.my_slider.value = 10.0

    assert "'my_slider.value' changed to '10.0'" in caplog.text
    assert "Slider changed to '10.0'" in caplog.text
    caplog.clear()

    service_instance.my_slider.max = 12.0

    assert "'my_slider.max' changed to '12.0'" in caplog.text
    caplog.clear()

    service_instance.my_slider.step_size = 0.1

    assert "'my_slider.step_size' changed to '0.1'" in caplog.text
    caplog.clear()

    # by overriding the getter only you can make the property read-only
    with pytest.raises(AttributeError):
        service_instance.my_slider.min = 1.1  # type: ignore[reportGeneralTypeIssues]
