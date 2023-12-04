import logging
from typing import Any, Literal

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
    type (Literal["int", "float"], optional):
        The type of the slider value. Determines if the value is an integer or float.
        Defaults to "float".

    Example:
    --------
    ```python
    class MyService(DataService):
        voltage = NumberSlider(1, 0, 10, 0.1, "int")

    # Modifying or accessing the voltage value:
    my_service = MyService()
    my_service.voltage.value = 5
    print(my_service.voltage.value)  # Output: 5
    ```
    """

    def __init__(  # noqa: PLR0913
        self,
        value: float = 0,
        min_: float = 0.0,
        max_: float = 100.0,
        step_size: float = 1.0,
        type_: Literal["int", "float"] = "float",
    ) -> None:
        super().__init__()
        if type_ not in {"float", "int"}:
            logger.error("Unknown type '%s'. Using 'float'.", type_)
            type_ = "float"

        self._type = type_
        self.step_size = step_size
        self.value = value
        self.min = min_
        self.max = max_

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ["value", "step_size"]:
            value = int(value) if self._type == "int" else float(value)
        elif not name.startswith("_"):
            value = float(value)

        return super().__setattr__(name, value)
