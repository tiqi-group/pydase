"""
The `components` module is a collection of specialized subclasses of the `DataService`
class that are designed to model different types of user interface components. These
classes can be used to represent the state of various UI elements in a data interface,
and provide a simple way to interact with these elements programmatically.

Each class in the `components` module corresponds to a specific type of UI element, such
as a slider, a file upload, a graph, etc. The state of these UI elements is maintained
by the instance variables of the respective classes. This allows you to keep track of
the user's interactions with the UI elements and update your application's state
accordingly.

You can use the classes in the `components` module as attributes of a `DataService`
subclass to model the state of your application's UI. Here is an example of how to use
the `NumberSlider` class:

```python
from components import NumberSlider

class MyService(DataService):
    voltage = NumberSlider(1, 0, 10, 0.1)

# Then, you can modify or access the voltage value like this:
my_service = MyService()
my_service.voltage.value = 5
print(my_service.voltage.value)  # Output: 5
```
"""

from pydase.components.coloured_enum import ColouredEnum
from pydase.components.device_connection import DeviceConnection
from pydase.components.image import Image
from pydase.components.number_slider import NumberSlider

__all__ = [
    "ColouredEnum",
    "DeviceConnection",
    "Image",
    "NumberSlider",
]
