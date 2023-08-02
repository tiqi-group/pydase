from ..data_service.data_service import DataService


class NumberSlider(DataService):
    """
    The `NumberSlider` class models and represents a UI component, such as a slider or
    a dial, in the context of a data interface. This could be useful in various
    applications, such as a lab setting where you might want to adjust a parameter
    (e.g., temperature, voltage) within a certain range, and want to ensure that the
    value is only adjusted in certain increments (`step_size`).

    You can use it as an attribute of a `DataService` subclass to model the state of a
    particular UI component. Here is an example of how to use the `NumberSlider` class:

    ```python
    class MyService(DataService):
        voltage = NumberSlider(1, 0, 10, 0.1)

    # Then, you can modify or access the voltage value like this:
    my_service = MyService()
    my_service.voltage.value = 5
    print(my_service.voltage.value)  # Output: 5
    ```

    Parameters:
    -----------
    value (float | int, optional):
        The initial value of the slider. Defaults to 0.
    min (int, optional):
        The minimum value of the slider. Defaults to 0.
    max (int, optional):
        The maximum value of the slider. Defaults to 100.
    step_size (float, optional):
        The increment/decrement step size of the slider. Defaults to 1.0.
    """

    def __init__(
        self,
        value: float | int = 0,
        min: int = 0,
        max: int = 100,
        step_size: float = 1.0,
    ) -> None:
        self.min = min
        self.max = max
        self.value = value
        self.step_size = step_size
        super().__init__()
