# Understanding Tasks

In `pydase`, a task is defined as an asynchronous function without arguments that is decorated with the `@task` decorator and contained in a class that inherits from `pydase.DataService`. These tasks usually contain a while loop and are designed to carry out periodic functions. For example, a task might be used to periodically read sensor data, update a database, or perform any other recurring job.

`pydase` allows you to control task execution via both the frontend and Python clients and can automatically start tasks upon initialization of the service. By using the `@task` decorator with the `autostart=True` argument in your service class, `pydase` will automatically start these tasks when the server is started. Here's an example:

```python
import pydase
from pydase.task.decorator import task


class SensorService(pydase.DataService):
    def __init__(self):
        super().__init__()
        self.readout_frequency = 1.0

    def _process_data(self, data: ...) -> None:
        ...

    def _read_from_sensor(self) -> Any:
        ...

    @task(autostart=True)
    async def read_sensor_data(self):
        while True:
            data = self._read_from_sensor()
            self._process_data(data)  # Process the data as needed
            await asyncio.sleep(self.readout_frequency)


if __name__ == "__main__":
    service = SensorService()
    pydase.Server(service=service).run()
```

In this example, `read_sensor_data` is a task that continuously reads data from a sensor. By decorating it with `@task(autostart=True)`, it will automatically start running when `pydase.Server(service).run()` is executed.

The `@task` decorator replaces the function with a task object that has `start()` and `stop()` methods. This means you can control the task execution directly using these methods. For instance, you can manually start or stop the task by calling `service.read_sensor_data.start()` and `service.read_sensor_data.stop()`, respectively.
