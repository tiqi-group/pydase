# pydase <!-- omit from toc -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/pydase/badge/?version=latest)](https://pydase.readthedocs.io/en/latest/?badge=latest)

`pydase` is a Python library designed to streamline the creation of services that interface with devices and data. It offers a unified API, simplifying the process of data querying and device interaction. Whether you're managing lab sensors, network devices, or any abstract data entity, `pydase` facilitates rapid service development and deployment.

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Defining a DataService](#defining-a-dataservice)
  - [Running the Server](#running-the-server)
  - [Accessing the Web Interface](#accessing-the-web-interface)
  - [Connecting to the Service via Python Client](#connecting-to-the-service-via-python-client)
    - [Tab Completion Support](#tab-completion-support)
    - [Integration within Another Service](#integration-within-another-service)
  - [RESTful API](#restful-api)
- [Understanding the Component System](#understanding-the-component-system)
  - [Built-in Type and Enum Components](#built-in-type-and-enum-components)
  - [Method Components](#method-components)
  - [DataService Instances (Nested Classes)](#dataservice-instances-nested-classes)
  - [Custom Components (`pydase.components`)](#custom-components-pydasecomponents)
    - [`DeviceConnection`](#deviceconnection)
      - [Customizing Connection Logic](#customizing-connection-logic)
      - [Reconnection Interval](#reconnection-interval)
    - [`Image`](#image)
    - [`NumberSlider`](#numberslider)
    - [`ColouredEnum`](#colouredenum)
    - [Extending with New Components](#extending-with-new-components)
- [Understanding Service Persistence](#understanding-service-persistence)
  - [Controlling Property State Loading with `@load_state`](#controlling-property-state-loading-with-load_state)
- [Understanding Tasks in pydase](#understanding-tasks-in-pydase)
- [Understanding Units in pydase](#understanding-units-in-pydase)
- [Using `validate_set` to Validate Property Setters](#using-validate_set-to-validate-property-setters)
- [Configuring pydase via Environment Variables](#configuring-pydase-via-environment-variables)
- [Customizing the Web Interface](#customizing-the-web-interface)
- [Logging in pydase](#logging-in-pydase)
  - [Changing the Log Level](#changing-the-log-level)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Features

<!-- no toc -->
- [Simple service definition through class-based interface](#defining-a-dataService)
- [Integrated web interface for interactive access and control of your service](#accessing-the-web-interface)
- [Support for programmatic control and interaction with your service](#connecting-to-the-service-via-python-client)
- [Component system bridging Python backend with frontend visual representation](#understanding-the-component-system)
- [Customizable styling for the web interface](#customizing-web-interface-style)
- [Saving and restoring the service state for service persistence](#understanding-service-persistence)
- [Automated task management with built-in start/stop controls and optional autostart](#understanding-tasks-in-pydase)
- [Support for units](#understanding-units-in-pydase)
- [Validating Property Setters](#using-validate_set-to-validate-property-setters)
<!-- Support for additional servers for specific use-cases -->

## Installation

<!--installation-start-->

Install `pydase` using [`poetry`](https://python-poetry.org/):

```bash
poetry add pydase
```

or `pip`:

```bash
pip install pydase
```

<!--installation-end-->

## Usage

<!--usage-start-->

Using `pydase` involves three main steps: defining a `DataService` subclass, running the server, and then connecting to the service either programmatically using `pydase.Client` or through the web interface.

### Defining a DataService

To use pydase, you'll first need to create a class that inherits from `DataService`. This class represents your custom data service, which will be exposed via a web server. Your class can implement class / instance attributes and synchronous and asynchronous tasks.

Here's an example:

```python
from pydase import DataService, Server
from pydase.utils.decorators import frontend


class Device(DataService):
    _current = 0.0
    _voltage = 0.0
    _power = False

    @property
    def current(self) -> float:
        # run code to get current
        return self._current

    @current.setter
    def current(self, value: float) -> None:
        # run code to set current
        self._current = value

    @property
    def voltage(self) -> float:
        # run code to get voltage
        return self._voltage

    @voltage.setter
    def voltage(self, value: float) -> None:
        # run code to set voltage
        self._voltage = value

    @property
    def power(self) -> bool:
        # run code to get power state
        return self._power

    @power.setter
    def power(self, value: bool) -> None:
        # run code to set power state
        self._power = value

    @frontend
    def reset(self) -> None:
        self.current = 0.0
        self.voltage = 0.0


if __name__ == "__main__":
    service = Device()
    Server(service).run()
```

In the above example, we define a Device class that extends DataService. We define a few properties (current, voltage, power) and their getter and setter methods.

### Running the Server

Once your DataService is defined, you can create an instance of it and run the server:

```python
from pydase import Server

# ... defining the Device class ...

if __name__ == "__main__":
    service = Device()
    Server(service).run()
```

This will start the server, making your Device service accessible on [http://localhost:8001](http://localhost:8001).

### Accessing the Web Interface

Once the server is running, you can access the web interface in a browser:

![Web Interface](./docs/images/Example_App.png)

In this interface, you can interact with the properties of your `Device` service.

### Connecting to the Service via Python Client

You can connect to the service using the `pydase.Client`. Below is an example of how to establish a connection to a service and interact with it:

```python
import pydase

# Replace the hostname and port with the IP address and the port of the machine where 
# the service is running, respectively
client_proxy = pydase.Client(hostname="<ip_addr>", port=8001).proxy

# After the connection, interact with the service attributes as if they were local
client_proxy.voltage = 5.0
print(client_proxy.voltage)  # Expected output: 5.0
```

This example demonstrates setting and retrieving the `voltage` attribute through the client proxy.
The proxy acts as a local representative of the remote service, enabling straightforward interaction.

The proxy class dynamically synchronizes with the server's exposed attributes. This synchronization allows the proxy to be automatically updated with any attributes or methods that the server exposes, essentially mirroring the server's API. This dynamic updating enables users to interact with the remote service as if they were working with a local object.

#### Tab Completion Support

In interactive environments such as Python interpreters and Jupyter notebooks, the proxy class supports tab completion, which allows users to explore available methods and attributes.

#### Integration within Another Service

You can also integrate a client proxy within another service. Here's how you can set it up:

```python
import pydase

class MyService(pydase.DataService):
    # Initialize the client without blocking the constructor
    proxy = pydase.Client(hostname="<ip_addr>", port=8001, block_until_connected=False).proxy

if __name__ == "__main__":
    service = MyService()
    # Create a server that exposes this service; adjust the web_port as needed
    server = pydase.Server(service, web_port=8002). run()
```

In this setup, the `MyService` class has a `proxy` attribute that connects to a `pydase` service located at `<ip_addr>:8001`.
The `block_until_connected=False` argument allows the service to start up even if the initial connection attempt fails.
This configuration is particularly useful in distributed systems where services may start in any order.

### RESTful API
The `pydase` RESTful API allows for standard HTTP-based interactions and provides access to various functionalities through specific routes. 

For example, you can get a value like this:

```python
import json

import requests

response = requests.get(
    "http://<hostname>:<port>/api/v1/get_value?access_path=<full_access_path>"
)
serialized_value = json.loads(response.text)
```

For more information, see [here](https://pydase.readthedocs.io/en/stable/user-guide/interaction/main/#restful-api).

<!--usage-end-->

## Understanding the Component System

<!-- Component User Guide Start -->

In `pydase`, components are fundamental building blocks that bridge the Python backend logic with frontend visual representation and interactions. This system can be understood based on the following categories:

### Built-in Type and Enum Components

`pydase` automatically maps standard Python data types to their corresponding frontend components:

- `str`: Translated into a `StringComponent` on the frontend.
- `int` and `float`: Manifested as the `NumberComponent`.
- `bool`: Rendered as a `ButtonComponent`.
- `list`: Each item displayed individually, named after the list attribute and its index.
- `dict`: Each key-value pair displayed individually, named after the dictionary attribute and its key. **Note** that the dictionary keys must be strings.
- `enum.Enum`: Presented as an `EnumComponent`, facilitating dropdown selection.

### Method Components
Within the `DataService` class of `pydase`, only methods devoid of arguments can be represented in the frontend, classified into two distinct categories

1. [**Tasks**](#understanding-tasks-in-pydase): Argument-free asynchronous functions, identified within `pydase` as tasks, are inherently designed for frontend interaction. These tasks are automatically rendered with a start/stop button, allowing users to initiate or halt the task execution directly from the web interface. 
2. **Synchronous Methods with `@frontend` Decorator**: Synchronous methods without arguments can also be presented in the frontend. For this, they have to be decorated with the `@frontend` decorator.

```python
import pydase
import pydase.components
import pydase.units as u
from pydase.utils.decorators import frontend


class MyService(pydase.DataService):
    @frontend
    def exposed_method(self) -> None:
        ...

    async def my_task(self) -> None:
        while True:
            # ...
```

![Method Components](docs/images/method_components.png)

You can still define synchronous tasks with arguments and call them using a python client. However, decorating them with the `@frontend` decorator will raise a `FunctionDefinitionError`. Defining a task with arguments will raise a `TaskDefinitionError`.
I decided against supporting function arguments for functions rendered in the frontend due to the following reasons:

1. Feature Request Pitfall: supporting function arguments create a bottomless pit of feature requests. As users encounter the limitations of supported types, demands for extending support to more complex types would grow.
2. Complexity in Supported Argument Types: while simple types like `int`, `float`, `bool` and `str` could be easily supported, more complicated types are not (representation, (de-)serialization).

### DataService Instances (Nested Classes)

Nested `DataService` instances offer an organized hierarchy for components, enabling richer applications. Each nested class might have its own attributes and methods, each mapped to a frontend component.

Here is an example:

```python
from pydase import DataService, Server


class Channel(DataService):
    def __init__(self, channel_id: int) -> None:
        super().__init__()
        self._channel_id = channel_id
        self._current = 0.0

    @property
    def current(self) -> float:
        # run code to get current
        result = self._current
        return result

    @current.setter
    def current(self, value: float) -> None:
        # run code to set current
        self._current = value


class Device(DataService):
    def __init__(self) -> None:
        super().__init__()
        self.channels = [Channel(i) for i in range(2)]


if __name__ == "__main__":
    service = Device()
    Server(service).run()
```

![Nested Classes App](docs/images/Nested_Class_App.png)

**Note** that defining classes within `DataService` classes is not supported (see [this issue](https://github.com/tiqi-group/pydase/issues/16)).

### Custom Components (`pydase.components`)

The custom components in `pydase` have two main parts:

- A **Python Component Class** in the backend, implementing the logic needed to set, update, and manage the component's state and data.
- A **Frontend React Component** that renders and manages user interaction in the browser.

Below are the components available in the `pydase.components` module, accompanied by their Python usage:

#### `DeviceConnection`

The `DeviceConnection` component acts as a base class within the `pydase` framework for managing device connections. It provides a structured approach to handle connections by offering a customizable `connect` method and a `connected` property. This setup facilitates the implementation of automatic reconnection logic, which periodically attempts reconnection whenever the connection is lost.

In the frontend, this class abstracts away the direct interaction with the `connect` method and the `connected` property. Instead, it showcases user-defined attributes, methods, and properties. When the `connected` status is `False`, the frontend displays an overlay that prompts manual reconnection through the `connect()` method. Successful reconnection removes the overlay.

```python
import pydase.components
import pydase.units as u


class Device(pydase.components.DeviceConnection):
    def __init__(self) -> None:
        super().__init__()
        self._voltage = 10 * u.units.V

    def connect(self) -> None:
        if not self._connected:
            self._connected = True

    @property
    def voltage(self) -> float:
        return self._voltage


class MyService(pydase.DataService):
    def __init__(self) -> None:
        super().__init__()
        self.device = Device()


if __name__ == "__main__":
    service_instance = MyService()
    pydase.Server(service_instance).run()
```

![DeviceConnection Component](docs/images/DeviceConnection_component.png)

##### Customizing Connection Logic

Users are encouraged to primarily override the `connect` method to tailor the connection process to their specific device. This method should adjust the `self._connected` attribute based on the outcome of the connection attempt:

```python
import pydase.components


class MyDeviceConnection(pydase.components.DeviceConnection):
    def __init__(self) -> None:
        super().__init__()
        # Add any necessary initialization code here

    def connect(self) -> None:
        # Implement device-specific connection logic here
        # Update self._connected to `True` if the connection is successful,
        # or `False` if unsuccessful
        ...
```

Moreover, if the connection status requires additional logic, users can override the `connected` property:

```python
import pydase.components

class MyDeviceConnection(pydase.components.DeviceConnection):
    def __init__(self) -> None:
        super().__init__()
        # Add any necessary initialization code here

    def connect(self) -> None:
        # Implement device-specific connection logic here
        # Ensure self._connected reflects the connection status accurately
        ...

    @property
    def connected(self) -> bool:
        # Implement custom logic to accurately report connection status
        return self._connected
```

##### Reconnection Interval

The `DeviceConnection` component automatically executes a task that checks for device availability at a default interval of 10 seconds. This interval is adjustable by modifying the `_reconnection_wait_time` attribute on the class instance.

#### `Image`

This component provides a versatile interface for displaying images within the application. Users can update and manage images from various sources, including local paths, URLs, and even matplotlib figures.

The component offers methods to load images seamlessly, ensuring that visual content is easily integrated and displayed within the data service.

```python
import matplotlib.pyplot as plt
import numpy as np
import pydase
from pydase.components.image import Image


class MyDataService(pydase.DataService):
    my_image = Image()


if __name__ == "__main__":
    service = MyDataService()
    # loading from local path
    service.my_image.load_from_path("/your/image/path/")

    # loading from a URL
    service.my_image.load_from_url("https://cataas.com/cat")

    # loading a matplotlib figure
    fig = plt.figure()
    x = np.linspace(0, 2 * np.pi)
    plt.plot(x, np.sin(x))
    plt.grid()
    service.my_image.load_from_matplotlib_figure(fig)

    pydase.Server(service).run()
```

![Image Component](docs/images/Image_component.png)

#### `NumberSlider`

The `NumberSlider` component in the `pydase` package provides an interactive slider interface for adjusting numerical values on the frontend. It is designed to support both numbers and quantities and ensures that values adjusted on the frontend are synchronized with the backend.

To utilize the `NumberSlider`, users should implement a class that derives from `NumberSlider`. This class can then define the initial values, minimum and maximum limits, step sizes, and additional logic as needed.

Here's an example of how to implement and use a custom slider:

```python
import pydase
import pydase.components


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
        """Slider value."""
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        if value < self._min or value > self._max:
            raise ValueError("Value is either below allowed min or above max value.")

        self._value = value


class MyService(pydase.DataService):
    def __init__(self) -> None:
        super().__init__()
        self.voltage = MySlider()


if __name__ == "__main__":
    service_instance = MyService()
    service_instance.voltage.value = 5
    print(service_instance.voltage.value)  # Output: 5
    pydase.Server(service_instance).run()
```

In this example, `MySlider` overrides the `min`, `max`, `step_size`, and `value` properties. Users can make any of these properties read-only by omitting the corresponding setter method.

![Slider Component](docs/images/Slider_component.png)

- Accessing parent class resources in `NumberSlider`

    In scenarios where you need the slider component to interact with or access resources from its parent class, you can achieve this by passing a callback function to it. This method avoids directly passing the entire parent class instance (`self`) and offers a more encapsulated approach. The callback function can be designed to utilize specific attributes or methods of the parent class, allowing the slider to perform actions or retrieve data in response to slider events.

    Here's an illustrative example:

    ```python
    from collections.abc import Callable

    import pydase
    import pydase.components


    class MySlider(pydase.components.NumberSlider):
        def __init__(
            self,
            value: float,
            on_change: Callable[[float], None],
        ) -> None:
            super().__init__(value=value)
            self._on_change = on_change

        # ... other properties ...

        @property
        def value(self) -> float:
            return self._value

        @value.setter
        def value(self, new_value: float) -> None:
            if new_value < self._min or new_value > self._max:
                raise ValueError("Value is either below allowed min or above max value.")
            self._value = new_value
            self._on_change(new_value)


    class MyService(pydase.DataService):
        def __init__(self) -> None:
            self.voltage = MySlider(
                5,
                on_change=self.handle_voltage_change,
            )

        def handle_voltage_change(self, new_voltage: float) -> None:
            print(f"Voltage changed to: {new_voltage}")
            # Additional logic here

    if __name__ == "__main__":
       service_instance = MyService()
       my_service.voltage.value = 7  # Output: "Voltage changed to: 7"
       pydase.Server(service_instance).run()
    ```

- Incorporating units in `NumberSlider`

    The `NumberSlider` is capable of [displaying units](#understanding-units-in-pydase) alongside values, enhancing its usability in contexts where unit representation is crucial. When utilizing `pydase.units`, you can specify units for the slider's value, allowing the component to reflect these units in the frontend.

    Here's how to implement a `NumberSlider` with unit display:

    ```python
    import pydase
    import pydase.components
    import pydase.units as u

    class MySlider(pydase.components.NumberSlider):
        def __init__(
            self,
            value: u.Quantity = 0.0 * u.units.V,
        ) -> None:
            super().__init__(value)

        @property
        def value(self) -> u.Quantity:
            return self._value

        @value.setter
        def value(self, value: u.Quantity) -> None:
            if value.m < self._min or value.m > self._max:
                raise ValueError("Value is either below allowed min or above max value.")
            self._value = value

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.voltage = MySlider()

    if __name__ == "__main__":
        service_instance = MyService()
        service_instance.voltage.value = 5 * u.units.V
        print(service_instance.voltage.value)  # Output: 5 V
        pydase.Server(service_instance).run()
    ```

#### `ColouredEnum`

This component provides a way to visually represent different states or categories in a data service using colour-coded options. It behaves similarly to a standard `Enum`, but the values encode colours in a format understood by CSS. The colours can be defined using various methods like Hexadecimal, RGB, HSL, and more.

If the property associated with the `ColouredEnum` has a setter function, the keys of the enum will be rendered as a dropdown menu, allowing users to interact and select different options. Without a setter function, the selected key will simply be displayed as a coloured box with text inside, serving as a visual indicator.

```python
import pydase
import pydase.components as pyc


class MyStatus(pyc.ColouredEnum):
    PENDING = "#FFA500"  # Hexadecimal colour (Orange)
    RUNNING = "#0000FF80"  # Hexadecimal colour with transparency (Blue)
    PAUSED = "rgb(169, 169, 169)"  # RGB colour (Dark Gray)
    RETRYING = "rgba(255, 255, 0, 0.3)"  # RGB colour with transparency (Yellow)
    COMPLETED = "hsl(120, 100%, 50%)"  # HSL colour (Green)
    FAILED = "hsla(0, 100%, 50%, 0.7)"  # HSL colour with transparency (Red)
    CANCELLED = "SlateGray"  # Cross-browser colour name (Slate Gray)


class StatusTest(pydase.DataService):
    _status = MyStatus.RUNNING

    @property
    def status(self) -> MyStatus:
        return self._status

    @status.setter
    def status(self, value: MyStatus) -> None:
        # do something ...
        self._status = value

# Modifying or accessing the status value:
my_service = StatusExample()
my_service.status = MyStatus.FAILED
```

![ColouredEnum Component](docs/images/ColouredEnum_component.png)

**Note** that each enumeration name and value must be unique.
This means that you should use different colour formats when you want to use a colour multiple times.

#### Extending with New Components

Users can also extend the library by creating custom components. This involves defining the behavior on the Python backend and the visual representation on the frontend. For those looking to introduce new components, the [guide on adding components](https://pydase.readthedocs.io/en/latest/dev-guide/Adding_Components/) provides detailed steps on achieving this.

<!-- Component User Guide End -->

## Understanding Service Persistence

`pydase` allows you to easily persist the state of your service by saving it to a file. This is especially useful when you want to maintain the service's state across different runs.

To save the state of your service, pass a `filename` keyword argument to the constructor of the `pydase.Server` class. If the file specified by `filename` does not exist, the state manager will create this file and store its state in it when the service is shut down. If the file already exists, the state manager will load the state from this file, setting the values of its attributes to the values stored in the file.

Here's an example:

```python
from pydase import DataService, Server

class Device(DataService):
    # ... defining the Device class ...


if __name__ == "__main__":
    service = Device()
    Server(service, filename="device_state.json").run()
```

In this example, the state of the `Device` service will be saved to `device_state.json` when the service is shut down. If `device_state.json` exists when the server is started, the state manager will restore the state of the service from this file.

### Controlling Property State Loading with `@load_state`

By default, the state manager only restores values for public attributes of your service. If you have properties that you want to control the loading for, you can use the `@load_state` decorator on your property setters. This indicates to the state manager that the value of the property should be loaded from the state file.

Here is how you can apply the `@load_state` decorator:

```python
from pydase import DataService
from pydase.data_service.state_manager import load_state

class Device(DataService):
    _name = "Default Device Name"

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    @load_state
    def name(self, value: str) -> None:
        self._name = value
```

With the `@load_state` decorator applied to the `name` property setter, the state manager will load and apply the `name` property's value from the file storing the state upon server startup, assuming it exists.

Note: If the service class structure has changed since the last time its state was saved, only the attributes and properties decorated with `@load_state` that have remained the same will be restored from the settings file.

## Understanding Tasks in pydase

In `pydase`, a task is defined as an asynchronous function without arguments contained in a class that inherits from `DataService`. These tasks usually contain a while loop and are designed to carry out periodic functions.

For example, a task might be used to periodically read sensor data, update a database, or perform any other recurring job. One core feature of `pydase` is its ability to automatically generate start and stop functions for these tasks. This allows you to control task execution via both the frontend and python clients, giving you flexible and powerful control over your service's operation.

Another powerful feature of `pydase` is its ability to automatically start tasks upon initialization of the service. By specifying the tasks and their arguments in the `_autostart_tasks` dictionary in your service class's `__init__` method, `pydase` will automatically start these tasks when the server is started. Here's an example:

```python
from pydase import DataService, Server

class SensorService(DataService):
    def __init__(self):
        super().__init__()
        self.readout_frequency = 1.0
        self._autostart_tasks["read_sensor_data"] = ()

    def _process_data(self, data: ...) -> None:
        ...

    def _read_from_sensor(self) -> Any:
        ...

    async def read_sensor_data(self):
        while True:
            data = self._read_from_sensor()
            self._process_data(data)  # Process the data as needed
            await asyncio.sleep(self.readout_frequency)


if __name__ == "__main__":
    service = SensorService()
    Server(service).run()
```

In this example, `read_sensor_data` is a task that continuously reads data from a sensor. By adding it to the `_autostart_tasks` dictionary, it will automatically start running when `Server(service).run()` is executed.
As with all tasks, `pydase` will generate `start_read_sensor_data` and `stop_read_sensor_data` methods, which can be called to manually start and stop the data reading task. The readout frequency can be updated using the `readout_frequency` attribute.

## Understanding Units in pydase

`pydase` integrates with the [`pint`](https://pint.readthedocs.io/en/stable/) package to allow you to work with physical quantities within your service. This enables you to define attributes with units, making your service more expressive and ensuring consistency in the handling of physical quantities.

You can define quantities in your `DataService` subclass using `pydase`'s `units` functionality.

Here's an example:

```python
from typing import Any

import pydase.units as u
from pydase import DataService, Server


class ServiceClass(DataService):
    voltage = 1.0 * u.units.V
    _current: u.Quantity = 1.0 * u.units.mA

    @property
    def current(self) -> u.Quantity:
        return self._current

    @current.setter
    def current(self, value: u.Quantity) -> None:
        self._current = value


if __name__ == "__main__":
    service = ServiceClass()

    service.voltage = 10.0 * u.units.V
    service.current = 1.5 * u.units.mA

    Server(service).run()
```

In the frontend, quantities are rendered as floats, with the unit displayed as additional text. This allows you to maintain a clear and consistent representation of physical quantities across both the backend and frontend of your service.
![Web interface with rendered units](./docs/images/Units_App.png)

Should you need to access the magnitude or the unit of a quantity, you can use the `.m` attribute or the `.u` attribute of the variable, respectively. For example, this could be necessary to set the periodicity of a task:

```python
import asyncio
from pydase import DataService, Server
import pydase.units as u


class ServiceClass(DataService):
    readout_wait_time = 1.0 * u.units.ms

    async def read_sensor_data(self):
        while True:
            print("Reading out sensor ...")
            await asyncio.sleep(self.readout_wait_time.to("s").m)


if __name__ == "__main__":
    service = ServiceClass()

    Server(service).run()
```

For more information about what you can do with the units, please consult the documentation of [`pint`](https://pint.readthedocs.io/en/stable/).

## Using `validate_set` to Validate Property Setters

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
    pydase.Server(Service()).run()
```

## Configuring pydase via Environment Variables

Configuring `pydase` through environment variables enhances flexibility, security, and reusability. This approach allows for easy adaptation of services across different environments without code changes, promoting scalability and maintainability. With that, it simplifies deployment processes and facilitates centralized configuration management. Moreover, environment variables enable separation of configuration from code, aiding in secure and collaborative development.

`pydase` offers various configurable options:

- **`ENVIRONMENT`**: Sets the operation mode to either "development" or "production". Affects logging behaviour (see [logging section](#logging-in-pydase)).
- **`SERVICE_CONFIG_DIR`**: Specifies the directory for service configuration files, like `web_settings.json`. This directory can also be used to hold user-defined configuration files. Default is the `config` folder in the service root folder. The variable can be accessed through:

    ```python
    import pydase.config
    pydase.config.ServiceConfig().config_dir
    ```

- **`SERVICE_WEB_PORT`**: Defines the port number for the web server. This has to be different for each services running on the same host. Default is 8001.
- **`GENERATE_WEB_SETTINGS`**: When set to true, generates / updates the `web_settings.json` file. If the file already exists, only new entries are appended.

Some of those settings can also be altered directly in code when initializing the server: 

```python
import pathlib

from pydase import Server
from your_service_module import YourService


server = Server(
    YourService(),
    web_port=8080,
    config_dir=pathlib.Path("other_config_dir"),  # note that you need to provide an argument of type pathlib.Path
    generate_web_settings=True
).run()
```

## Customizing the Web Interface

`pydase` allows you to enhance the user experience by customizing the web interface's appearance through

1. a custom CSS file, and
2. tailoring the frontend component layout and display style.

You can also provide a custom frontend source if you need even more flexibility.

For details, please see [here](https://pydase.readthedocs.io/en/stable/user-guide/interaction/main/#customization-options).

## Logging in pydase

The `pydase` library organizes its loggers on a per-module basis, mirroring the Python package hierarchy. This structured approach allows for granular control over logging levels and behaviour across different parts of the library.

### Changing the Log Level

You have two primary ways to adjust the log levels in `pydase`:

1. directly targeting `pydase` loggers

   You can set the log level for any `pydase` logger directly in your code. This method is useful for fine-tuning logging levels for specific modules within `pydase`. For instance, if you want to change the log level of the main `pydase` logger or target a submodule like `pydase.data_service`, you can do so as follows:

   ```python
   # <your_script.py>
   import logging

   # Set the log level for the main pydase logger
   logging.getLogger("pydase").setLevel(logging.INFO)

   # Optionally, target a specific submodule logger
   # logging.getLogger("pydase.data_service").setLevel(logging.DEBUG)

   # Your logger for the current script
   logger = logging.getLogger(__name__)
   logger.info("My info message.")
   ```

   This approach allows for specific control over different parts of the `pydase` library, depending on your logging needs.

2. using the `ENVIRONMENT` environment variable

   For a more global setting that affects the entire `pydase` library, you can utilize the `ENVIRONMENT` environment variable. Setting this variable to "production" will configure all `pydase` loggers to only log messages of level "INFO" and above, filtering out more verbose logging. This is particularly useful for production environments where excessive logging can be overwhelming or unnecessary.

   ```bash
   ENVIRONMENT="production" python -m <module_using_pydase>
   ```

   In the absence of this setting, the default behavior is to log everything of level "DEBUG" and above, suitable for development environments where more detailed logs are beneficial.

**Note**: It is recommended to avoid calling the `pydase.utils.logging.setup_logging` function directly, as this may result in duplicated logging messages.

## Documentation

The full documentation provides more detailed information about `pydase`, including advanced usage examples, API references, and tips for troubleshooting common issues. See the [full documentation](https://pydase.readthedocs.io/en/latest/) for more information.

## Contributing

We welcome contributions! Please see [contributing.md](https://pydase.readthedocs.io/en/latest/about/contributing/) for details on how to contribute.

## License

`pydase` is licensed under the [MIT License](https://github.com/tiqi-group/pydase/blob/main/LICENSE).
