# Using `validate_set` to Validate Property Setters

The `validate_set` decorator ensures that a property setter reads back the set value using the property getter and checks it against the desired value.
This decorator can be used to validate that a parameter has been correctly set on a device within a specified precision and timeout.

The decorator takes two keyword arguments: `timeout` and `precision`. The `timeout` argument specifies the maximum time (in seconds) to wait for the value to be within the precision boundary.
If the value is not within the precision boundary after this time, an exception is raised.
The `precision` argument defines the acceptable deviation from the desired value.
If `precision` is `None`, the value must be exact.
For example, if `precision` is set to `1e-5`, the value read from the device must be within ±0.00001 of the desired value.

Here’s how to use the `validate_set` decorator in a `DataService` class:

```python
import pydase
from pydase.observer_pattern.observable.decorators import validate_set


class Service(pydase.DataService):
    def __init__(self) -> None:
        super().__init__()
        self._device = RemoteDevice()  # dummy class

    @property
    def value(self) -> float:
        # Implement how to get the value from the remote device...
        return self._device.value

    @value.setter
    @validate_set(timeout=1.0, precision=1e-5)
    def value(self, value: float) -> None:
        # Implement how to set the value on the remote device...
        self._device.value = value


if __name__ == "__main__":
    pydase.Server(service=Service()).run()
```
