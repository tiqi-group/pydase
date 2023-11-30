from pydase.components.number_slider import NumberSlider
from pydase.data_service.data_service import DataService
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pytest import LogCaptureFixture


def test_NumberSlider(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        number_slider = NumberSlider(1, 0, 10, 1)
        int_number_slider = NumberSlider(1, 0, 10, 1, "int")

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    assert service_instance.number_slider.value == 1
    assert isinstance(service_instance.number_slider.value, float)
    assert service_instance.number_slider.min == 0
    assert isinstance(service_instance.number_slider.min, float)
    assert service_instance.number_slider.max == 10
    assert isinstance(service_instance.number_slider.max, float)
    assert service_instance.number_slider.step_size == 1
    assert isinstance(service_instance.number_slider.step_size, float)

    assert service_instance.int_number_slider.value == 1
    assert isinstance(service_instance.int_number_slider.value, int)
    assert service_instance.int_number_slider.step_size == 1
    assert isinstance(service_instance.int_number_slider.step_size, int)

    service_instance.number_slider.value = 10.0
    service_instance.int_number_slider.value = 10.1

    assert "'number_slider.value' changed to '10.0'" in caplog.text
    assert "'int_number_slider.value' changed to '10'" in caplog.text
    caplog.clear()

    service_instance.number_slider.min = 1.1

    assert "'number_slider.min' changed to '1.1'" in caplog.text


def test_init_error(caplog: LogCaptureFixture) -> None:
    number_slider = NumberSlider(type_="str")  # type: ignore # noqa

    assert "Unknown type 'str'. Using 'float'" in caplog.text
