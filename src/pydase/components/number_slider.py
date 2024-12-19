import logging
from typing import Any

from pydase.data_service.data_service import DataService

logger = logging.getLogger(__name__)


class NumberSlider(DataService):
    """
    This class models a UI slider for a data service, allowing for adjustments of a
    parameter within a specified range and increments.

    Args:
        value:
            The initial value of the slider. Defaults to 0.0.
        min_:
            The minimum value of the slider. Defaults to 0.0.
        max_:
            The maximum value of the slider. Defaults to 100.0.
        step_size:
            The increment/decrement step size of the slider. Defaults to 1.0.

    Example:
        ```python
        class MySlider(pydase.components.NumberSlider):
            def __init__(
                self,
                value: float = 0.0,
                min_: float = 0.0,
                max_: float = 100.0,
                step_size: float = 1.0,
            ) -> None:
                super().__init__(value, min_, max_, step_size)

            @property
            def min(self) -> float:
                return self._min

            @min.setter
            def min(self, value: float) -> None:
                self._min = value

            @property
            def max(self) -> float:
                return self._max

            @max.setter
            def max(self, value: float) -> None:
                self._max = value

            @property
            def step_size(self) -> float:
                return self._step_size

            @step_size.setter
            def step_size(self, value: float) -> None:
                self._step_size = value

            @property
            def value(self) -> float:
                return self._value

            @value.setter
            def value(self, value: float) -> None:
                if value < self._min or value > self._max:
                    raise ValueError(
                        "Value is either below allowed min or above max value."
                    )

                self._value = value

        class MyService(pydase.DataService):
            def __init__(self) -> None:
                self.voltage = MyService()

        # Modifying or accessing the voltage value:
        my_service = MyService()
        my_service.voltage.value = 5
        print(my_service.voltage.value)  # Output: 5
        ```
    """

    def __init__(
        self,
        value: Any = 0.0,
        min_: Any = 0.0,
        max_: Any = 100.0,
        step_size: Any = 1.0,
    ) -> None:
        super().__init__()
        self._step_size = step_size
        self._value = value
        self._min = min_
        self._max = max_

    @property
    def min(self) -> Any:
        """The min property."""
        return self._min

    @property
    def max(self) -> Any:
        """The min property."""
        return self._max

    @property
    def step_size(self) -> Any:
        """The min property."""
        return self._step_size

    @property
    def value(self) -> Any:
        """The value property."""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self._value = value
