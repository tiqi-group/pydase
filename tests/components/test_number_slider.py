from pytest import CaptureFixture, LogCaptureFixture

from pydase.components.number_slider import NumberSlider
from pydase.data_service.data_service import DataService

from .. import caplog  # noqa


def test_NumberSlider(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        number_slider = NumberSlider(1, 0, 10, 1)
        int_number_slider = NumberSlider(1, 0, 10, 1, "int")

    service = ServiceClass()

    assert service.number_slider.value == 1
    assert isinstance(service.number_slider.value, float)
    assert service.number_slider.min == 0
    assert isinstance(service.number_slider.min, float)
    assert service.number_slider.max == 10
    assert isinstance(service.number_slider.max, float)
    assert service.number_slider.step_size == 1
    assert isinstance(service.number_slider.step_size, float)

    assert service.int_number_slider.value == 1
    assert isinstance(service.int_number_slider.value, int)
    assert service.int_number_slider.step_size == 1
    assert isinstance(service.int_number_slider.step_size, int)

    service.number_slider.value = 10.0
    service.int_number_slider.value = 10.1

    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.number_slider.value = 10.0",
            "ServiceClass.int_number_slider.value = 10",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output

    service.number_slider.min = 1.1

    captured = capsys.readouterr()

    expected_output = sorted(
        [
            "ServiceClass.number_slider.min = 1.1",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))  # type: ignore
    assert actual_output == expected_output


def test_init_error(caplog: LogCaptureFixture) -> None:  # noqa
    number_slider = NumberSlider(type="str")  # type: ignore # noqa

    assert "Unknown type 'str'. Using 'float'" in caplog.text
