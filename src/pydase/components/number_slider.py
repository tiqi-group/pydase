import logging

from pydase.data_service.data_service import DataService

logger = logging.getLogger(__name__)


class NumberSlider(DataService):
    """
    This class models a UI slider for a data service, allowing for adjustments of a
    parameter within a specified range and increments.

    Parameters:
    -----------
    value (float, optional):
        The initial value of the slider. Defaults to 0.
    min (float, optional):
        The minimum value of the slider. Defaults to 0.
    max (float, optional):
        The maximum value of the slider. Defaults to 100.
    step_size (float, optional):
        The increment/decrement step size of the slider. Defaults to 1.0.

    Example:
    --------
    ```python
    class MyService(DataService):
        voltage = NumberSlider(1, 0, 10, 0.1)

    # Modifying or accessing the voltage value:
    my_service = MyService()
    my_service.voltage.value = 5
    print(my_service.voltage.value)  # Output: 5
    ```
    """

    def __init__(
        self,
        value: float = 0,
        min_: float = 0.0,
        max_: float = 100.0,
        step_size: float = 1.0,
    ) -> None:
        super().__init__()
        self._step_size = step_size
        self._value = value
        self._min = min_
        self._max = max_

    @property
    def min(self) -> float:
        """The min property."""
        return self._min

    @min.setter
    def min(self, value: float) -> None:
        self._min = value

    @property
    def max(self) -> float:
        """The min property."""
        return self._max

    @max.setter
    def max(self, value: float) -> None:
        self._max = value

    @property
    def step_size(self) -> float:
        """The min property."""
        return self._step_size

    @step_size.setter
    def step_size(self, value: float) -> None:
        self._step_size = value

    @property
    def value(self) -> float:
        """The value property."""
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        self._value = value
