# pydase (Python Data Service)

`pydase` is a Python library for creating data service servers with integrated web and RPC servers. It's designed to handle the management of data structures, automated tasks, and callbacks, and provides built-in functionality for serving data over different protocols.

## Features

- Integrated web and RPC servers
- Automated task management
- Event-based callback functionality for real-time updates
- Built-in support for serving data over different protocols
- Support for additional servers for specific use-cases

## Installation

Install pydase using [`poetry`](python-poetry.org/):

```bash
poetry add git+https://github.com/tiqi-group/pydase.git
```

## Usage

To use pydase, you will need to create a class that inherits from `DataService`. This class will be exposed via RPC (using rpyc) and a web server. The class can implement class / instance attributes and synchronous and asynchronous tasks.

Here's an example:

```python
from pydase import DataService, Server
from pydase.components import NumberSlider

class Device(DataService):

    _current = 0.0
    _voltage = 0.0
    _power = False

    @property
    def current(self):
        # run code to get current
        return self._current

    @current.setter
    def current(self, value):
        # run code to set current
        self._current = value

    @property
    def voltage(self):
        # run code to get voltage
        return self._voltage

    @voltage.setter
    def voltage(self, value):
        # run code to set voltage
        self._voltage = value

    @property
    def power(self):
        # run code to get power state
        return self._power

    @power.setter
    def power(self, value):
        # run code to set power state
        self._power = value

    def reset(self):
        self.current = 0.0
        self.voltage = 0.0


if __name__ == "__main__":
    service = ServiceClass()
    Server(service).run()
```

## Documentation

For more details about usage and features, see the [full documentation](URL_TO_YOUR_DOCUMENTATION).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](URL_TO_YOUR_CONTRIBUTING_GUIDELINES) for details on how to contribute.

## License

`pydase` is licensed under the [MIT License](./LICENSE).