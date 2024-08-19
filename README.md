<!--introduction-start-->
# pydase <!-- omit from toc -->

[![Version](https://img.shields.io/pypi/v/pydase?style=flat)](https://pypi.org/project/pydase/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pydase)](https://pypi.org/project/pydase/)
[![Documentation Status](https://readthedocs.org/projects/pydase/badge/?version=latest)](https://pydase.readthedocs.io/en/latest/?badge=stable)
[![License: MIT](https://img.shields.io/github/license/tiqi-group/pydase)](https://github.com/tiqi-group/pydase/blob/main/LICENSE)

`pydase` is a Python library that simplifies the creation of remote control interfaces for Python objects. It exposes the public attributes of a user-defined class via a Socket.IO web server, ensuring they are always in sync with the service state. You can interact with these attributes using an RPC client, a RESTful API, or a web browser. The web browser frontend is auto-generated, displaying components that correspond to each public attribute of the class for direct interaction.
`pydase` implements an observer pattern and to provide real-time updates, ensuring that changes to the class attributes are reflected across all clients.

Whether you're managing lab sensors, network devices, or any abstract data entity, `pydase` facilitates service development and deployment.

## Features

<!-- no toc -->
- [Simple service definition through class-based interface](#defining-a-dataService)
- [Auto-generated web interface for interactive access and control of your service](#accessing-the-web-interface)
- [Python RPC client](#connecting-to-the-service-via-python-rpc-client)
- [Customizable web interface](#customizing-the-web-interface)
- [Saving and restoring the service state](https://pydase.readthedocs.io/en/latest/user-guide/Service_Persistence)
- [Automated task management with built-in start/stop controls and optional autostart](#understanding-tasks-in-pydase)
- [Support for units](#understanding-units-in-pydase)
- [Validating Property Setters](#using-validate_set-to-validate-property-setters)
<!-- Support for additional servers for specific use-cases -->

<!--introduction-end-->

<!--getting-started-start-->

## Installation


Install `pydase` using [`poetry`](https://python-poetry.org/):

```bash
poetry add pydase
```

or `pip`:

```bash
pip install pydase
```


## Usage


Using `pydase` involves three main steps: defining a `pydase.DataService` subclass, running the server, and then connecting to the service either programmatically using `pydase.Client` or through the web interface.

### Defining a DataService

To use `pydase`, you'll first need to create a class that inherits from `pydase.DataService`.
This class represents your custom service, which will be exposed via a web server.<br>
Your class can implement synchronous and asynchronous methods, some [built-in types](https://docs.python.org/3/library/stdtypes.html) (like `int`, `float`, `str`, `bool`, `list` or `dict`) and [other components](https://pydase.readthedocs.io/en/latest/user-guide/Components/#custom-components-pydasecomponents) as attributes.
For more information, please refer to the [documentation](https://pydase.readthedocs.io/en/latest/user-guide/Components/).

Here's an example:

```python
import pydase
from pydase.utils.decorators import frontend


class Device(pydase.DataService):
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
    pydase.Server(service=service).run()
```

In the above example, we define a `Device` class that inherits from `pydase.DataService`. 
We define a few properties (current, voltage, power) and their getter and setter methods.

### Running the Server

Once your service class is defined, you can create an instance of it and run the server:

```python
import pydase

# ... defining the Device class ...

if __name__ == "__main__":
    service = Device()
    pydase.Server(service=service).run()
```

This will start the server, making your `Device` service accessible on [http://localhost:8001](http://localhost:8001).

### Accessing the Web Interface

Once the server is running, you can access the web interface in a browser:

![Web Interface](./docs/images/Example_App.png)

In this interface, you can interact with the properties of your `Device` service.

### Connecting to the Service via Python RPC Client

You can connect to the service using the `pydase.Client`. Below is an example of how to establish a connection to a service and interact with it:

```python
import pydase

# Replace the hostname and port with the IP address and the port of the machine where 
# the service is running, respectively
client_proxy = pydase.Client(url="ws://<ip_addr>:<service_port>").proxy
# client_proxy = pydase.Client(url="wss://your-domain.ch").proxy  # if your service uses ssl-encryption

# After the connection, interact with the service attributes as if they were local
client_proxy.voltage = 5.0
print(client_proxy.voltage)  # Expected output: 5.0
```

This example demonstrates setting and retrieving the `voltage` attribute through the client proxy.
The proxy acts as a local representative of the remote service, enabling straightforward interaction.

The proxy class dynamically synchronizes with the server's exposed attributes. This synchronization allows the proxy to be automatically updated with any attributes or methods that the server exposes, essentially mirroring the server's API. This dynamic updating enables users to interact with the remote service as if they were working with a local object.

The RPC client also supports tab completion support in the interpreter, can be used as a context manager and integrates very well with other pydase services. For more information, please refer to the [documentation](https://pydase.readthedocs.io/en/latest/user-guide/interaction/main/#python-client).

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

<!--getting-started-end-->

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
