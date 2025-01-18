# Understanding Tasks

In `pydase`, a task is defined as an asynchronous function without arguments that is decorated with the [`@task`][pydase.task.decorator.task] decorator and contained in a class that inherits from [`pydase.DataService`][pydase.DataService]. These tasks usually contain a while loop and are designed to carry out periodic functions. For example, a task might be used to periodically read sensor data, update a database, or perform any other recurring job.

`pydase` allows you to control task execution via both the frontend and Python clients and can automatically start tasks upon initialization of the service. By using the [`@task`][pydase.task.decorator.task] decorator with the `autostart=True` argument in your service class, `pydase` will automatically start these tasks when the server is started. Here's an example:

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

## Task Lifecycle Control

The [`@task`][pydase.task.decorator.task] decorator replaces the function with a task object that has `start()` and `stop()` methods. This means you can control the task execution directly using these methods. For instance, you can manually start or stop the task by calling `service.read_sensor_data.start()` and `service.read_sensor_data.stop()`, respectively.

## Advanced Task Options

The [`@task`][pydase.task.decorator.task] decorator supports several options inspired by systemd unit services, allowing fine-grained control over task behavior:

- **`autostart`**: Automatically starts the task when the service initializes. Defaults to `False`.
- **`restart_on_exception`**: Configures whether the task should restart if it exits due to an exception (other than `asyncio.CancelledError`). Defaults to `True`.
- **`restart_sec`**: Specifies the delay (in seconds) before restarting a failed task. Defaults to `1.0`.
- **`start_limit_interval_sec`**: Configures a time window (in seconds) for rate limiting task restarts. If the task restarts more than `start_limit_burst` times within this interval, it will no longer restart. Defaults to `None` (disabled).
- **`start_limit_burst`**: Defines the maximum number of restarts allowed within the interval specified by `start_limit_interval_sec`. Defaults to `3`.
- **`exit_on_failure`**: If set to `True`, the service will exit if the task fails and either `restart_on_exception` is `False` or the start rate limiting is exceeded. Defaults to `False`.

### Example with Advanced Options

Here is an example showcasing advanced task options:

```python
import pydase
from pydase.task.decorator import task


class AdvancedTaskService(pydase.DataService):
    def __init__(self):
        super().__init__()

    @task(
        autostart=True,
        restart_on_exception=True,
        restart_sec=2.0,
        start_limit_interval_sec=10.0,
        start_limit_burst=5,
        exit_on_failure=True,
    )
    async def critical_task(self):
        while True:
            raise Exception("Critical failure")


if __name__ == "__main__":
    service = AdvancedTaskService()
    pydase.Server(service=service).run()
```
