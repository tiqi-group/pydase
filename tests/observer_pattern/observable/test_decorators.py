import asyncio
import threading

import pytest

import pydase
from pydase.observer_pattern.observable.decorators import validate_set


def linspace(start: float, stop: float, n: int):
    if n == 1:
        yield stop
        return
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i


def asyncio_loop_thread(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()


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


def test_validate_set_timeout(caplog: pytest.LogCaptureFixture) -> None:
    class RemoteDevice:
        def __init__(self) -> None:
            self._value = 0.0
            self.loop = asyncio.new_event_loop()
            self._lock = asyncio.Lock()
            self.thread = threading.Thread(
                target=asyncio_loop_thread, args=(self.loop,), daemon=True
            )
            self.thread.start()

        def close_connection(self) -> None:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()

        @property
        def value(self) -> float:
            future = asyncio.run_coroutine_threadsafe(self._get_value(), self.loop)
            return future.result()

        async def _get_value(self) -> float:
            return self._value

        @value.setter
        def value(self, value: float) -> None:
            self.loop.create_task(self.set_value(value))

        async def set_value(self, value: float) -> None:
            for i in linspace(self._value, value, 10):
                self._value = i
                await asyncio.sleep(0.01)

    class Service(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._driver = RemoteDevice()

        @property
        def value_1(self) -> float:
            return self._driver.value

        @value_1.setter
        @validate_set(timeout=0.01)
        def value_1(self, value: float) -> None:
            self._driver.value = value

        @property
        def value_2(self) -> float:
            return self._driver.value

        @value_2.setter
        @validate_set(timeout=0.11)
        def value_2(self, value: float) -> None:
            self._driver.value = value

    service_instance = Service()

    with pytest.raises(ValueError) as exc_info:
        service_instance.value_1 = 2.0
        assert "Failed to set value to 2.0 within 0.5 seconds. Current value:" in str(
            exc_info
        )

    service_instance.value_2 = 3.0  # no assertion raised
    service_instance._driver.close_connection()
