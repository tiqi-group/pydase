# Understanding Tasks

In `pydase`, a task is defined as an asynchronous function without arguments contained in a class that inherits from `pydase.DataService`. These tasks usually contain a while loop and are designed to carry out periodic functions.

For example, a task might be used to periodically read sensor data, update a database, or perform any other recurring job. One core feature of `pydase` is its ability to automatically generate start and stop functions for these tasks. This allows you to control task execution via both the frontend and python clients, giving you flexible and powerful control over your service's operation.

Another powerful feature of `pydase` is its ability to automatically start tasks upon initialization of the service. By specifying the tasks and their arguments in the `_autostart_tasks` dictionary in your service class's `__init__` method, `pydase` will automatically start these tasks when the server is started. Here's an example:

```python
import pydase


class SensorService(pydase.DataService):
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
    pydase.Server(service=service).run()
```

In this example, `read_sensor_data` is a task that continuously reads data from a sensor. By adding it to the `_autostart_tasks` dictionary, it will automatically start running when `pydase.Server(service).run()` is executed.
As with all tasks, `pydase` will generate `start_read_sensor_data` and `stop_read_sensor_data` methods, which can be called to manually start and stop the data reading task. The readout frequency can be updated using the `readout_frequency` attribute.

