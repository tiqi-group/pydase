# Understanding Service Persistence

`pydase` allows you to easily persist the state of your service by saving it to a file. This is especially useful when you want to maintain the service's state across different runs.

To save the state of your service, pass a `filename` keyword argument to the constructor of the `pydase.Server` class. If the file specified by `filename` does not exist, the state manager will create this file and store its state in it when the service is shut down. If the file already exists, the state manager will load the state from this file, setting the values of its attributes to the values stored in the file.

Here's an example:

```python
import pydase

class Device(pydase.DataService):
    # ... defining the Device class ...


if __name__ == "__main__":
    service = Device()
    pydase.Server(service=service, filename="device_state.json").run()
```

In this example, the state of the `Device` service will be saved to `device_state.json` when the service is shut down. If `device_state.json` exists when the server is started, the state manager will restore the state of the service from this file.

## Controlling Property State Loading with `@load_state`

By default, the state manager only restores values for public attributes of your service. If you have properties that you want to control the loading for, you can use the `@load_state` decorator on your property setters. This indicates to the state manager that the value of the property should be loaded from the state file.

Here is how you can apply the `@load_state` decorator:

```python
import pydase
from pydase.data_service.state_manager import load_state

class Device(pydase.DataService):
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

