# Understanding Service Persistence

`pydase` allows you to easily persist the state of your service by saving it to a file. This is especially useful when you want to maintain the service's state across different runs.

To enable persistence, pass a `filename` keyword argument to the constructor of the [`pydase.Server`][pydase.Server] class. The `filename` specifies the file where the state will be saved:

- If the file **does not exist**, it will be created and populated with the current state when the service shuts down or saves.
- If the file **already exists**, the state manager will **load** the saved values into the service at startup.

Here’s an example:

```python
import pydase

class Device(pydase.DataService):
    # ... define your service class ...

if __name__ == "__main__":
    service = Device()
    pydase.Server(service=service, filename="device_state.json").run()
```

In this example, the service state will be automatically loaded from `device_state.json` at startup (if it exists), and saved to the same file periodically and upon shutdown.

## Automatic Periodic State Saving

When a `filename` is provided, `pydase` automatically enables **periodic autosaving** of the service state to that file. This ensures that the current state is regularly persisted, reducing the risk of data loss during unexpected shutdowns.

The autosave happens every 30 seconds by default. You can customize the interval using the `autosave_interval` argument (in seconds):

```python
pydase.Server(
    service=service,
    filename="device_state.json",
    autosave_interval=10.0,  # save every 10 seconds
).run()
```

To disable automatic saving, set `autosave_interval` to `None`.

## Controlling Property State Loading with `@load_state`

By default, the state manager only restores values for public attributes of your service (i.e. *it does not restore property values*). If you have properties that you want to control the loading for, you can use the [`@load_state`][pydase.data_service.state_manager.load_state] decorator on your property setters. This indicates to the state manager that the value of the property should be loaded from the state file.

Example:

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

With the `@load_state` decorator applied to the `name` property setter, the state manager will load and apply the `name` property's value from the file upon server startup.

**Note**: If the structure of your service class changes between saves, only properties decorated with `@load_state` and unchanged public attributes will be restored safely.
