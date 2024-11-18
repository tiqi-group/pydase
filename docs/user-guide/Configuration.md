
# Configuring `pydase`

## Do I Need to Configure My `pydase` Service?

`pydase` services work out of the box without requiring any configuration. However, you
might want to change some options, such as the web server port or logging level. To 
accommodate such customizations, `pydase` allows configuration through environment 
variables - avoiding hard-coded settings in your service code.

Why should you avoid hard-coding configurations? Here are two reasons:

1. **Security**:  
    Protect sensitive information, such as usernames and passwords. By using environment
    variables, your service code can remain public while keeping private information 
    secure.

2. **Reusability**:  
    Services often need to be reused in different environments. For example, you might
    deploy multiple instances of a service (e.g., for different sensors in a lab). By 
    separating configuration from code, you can adapt the service to new requirements 
    without modifying its codebase.

Next, we’ll walk you through the environment variables `pydase` supports and provide an
example of how to separate service code from configuration.

## Configuring `pydase` Using Environment Variables

`pydase` provides the following environment variables for customization:

- **`ENVIRONMENT`**:  
  Defines the operation mode (`"development"` or `"production"`), which influences 
  behaviour such as logging (see [Logging in pydase](https://github.com/tiqi-group/pydase?tab=readme-ov-file#logging-in-pydase)).

- **`SERVICE_CONFIG_DIR`**:  
  Specifies the directory for configuration files (e.g., `web_settings.json`). Defaults
  to the `config` folder in the service root. Access this programmatically using:

    ```python
    import pydase.config
    pydase.config.ServiceConfig().config_dir
    ```

- **`SERVICE_WEB_PORT`**:  
  Defines the web server’s port. Ensure each service on the same host uses a unique 
  port. Default: `8001`.

- **`GENERATE_WEB_SETTINGS`**:  
  When `true`, generates or updates the `web_settings.json` file. Existing entries are 
  preserved, and new entries are appended.

### Configuring `pydase` via Keyword Arguments

Some settings can also be overridden directly in your service code using keyword 
arguments when initializing the server. This allows for flexibility in code-based 
configuration:

```python
import pathlib
from pydase import Server
from your_service_module import YourService

server = Server(
    YourService(),
    web_port=8080,                             # Overrides SERVICE_WEB_PORT
    config_dir=pathlib.Path("custom_config"),  # Overrides SERVICE_CONFIG_DIR
    generate_web_settings=True                 # Overrides GENERATE_WEB_SETTINGS
).run()
```

## Separating Service Code from Configuration

To decouple configuration from code, `pydase` utilizes `confz` for configuration 
management. Below is an example that demonstrates how to configure a `pydase` service 
for a sensor readout application.

### Scenario: Configuring a Sensor Service

Imagine you have multiple sensors distributed across your lab. You need to configure 
each service instance with:

1. **Hostname**: The hostname or IP address of the sensor.
2. **Authentication Token**: A token or credentials to authenticate with the sensor.
3. **Readout Interval**: A periodic interval to read sensor data and log it to a 
  database.

Given the repository structure:

```bash title="Service Repository Structure"
my_sensor
├── pyproject.toml        
├── README.md             
└── src                   
    └── my_sensor       
        ├── my_sensor.py
        ├── config.py     
        ├── __init__.py   
        └── __main__.py   
```

Your service might look like this:

### Configuration

Define the configuration using `confz`:

```python title="src/my_sensor/config.py"
import confz
from pydase.config import ServiceConfig

class MySensorConfig(confz.BaseConfig):
    instance_name: str
    hostname: str
    auth_token: str
    readout_interval_s: float

    CONFIG_SOURCES = confz.FileSource(file=ServiceConfig().config_dir / "config.yaml")
```

This class defines configurable parameters and loads values from a `config.yaml` file
located in the service’s configuration directory (which is configurable through an 
environment variable, see [above](#configuring-pydase-using-environment-variables)).  
A sample YAML file might look like this:

```yaml title="config.yaml"
instance_name: my-sensor-service-01
hostname: my-sensor-01.example.com
auth_token: my-secret-authentication-token
readout_interval_s: 5
```

### Service Implementation

Your service implementation might look like this:

```python title="src/my_sensor/my_sensor.py"
import asyncio
import http.client
import json
import logging
from typing import Any

import pydase.components
import pydase.units as u
from pydase.task.decorator import task

from my_sensor.config import MySensorConfig

logger = logging.getLogger(__name__)


class MySensor(pydase.DataService):
    def __init__(self) -> None:
        super().__init__()
        self.readout_interval_s: u.Quantity = (
            MySensorConfig().readout_interval_s * u.units.s
        )

    @property
    def hostname(self) -> str:
        """Hostname of the sensor. Read-only."""
        return MySensorConfig().hostname

    def _get_data(self) -> dict[str, Any]:
        """Fetches sensor data via an HTTP GET request. It passes the authentication 
        token as "Authorization" header."""

        connection = http.client.HTTPConnection(self.hostname, timeout=10)
        connection.request(
            "GET", "/", headers={"Authorization": MySensorConfig().auth_token}
        )
        response = connection.getresponse()
        connection.close()

        return json.loads(response.read())

    @task(autostart=True)
    async def get_and_log_sensor_values(self) -> None:
        """Periodically fetches and logs sensor data."""
        while True:
            try:
                data = self._get_data()
                # Write data to database using MySensorConfig().instance_name ...
            except Exception as e:
                logger.error(
                    "Error occurred, retrying in %s seconds. Error: %s",
                    self.readout_interval_s.m,
                    e,
                )
            await asyncio.sleep(self.readout_interval_s.m)
```

### Starting the Service

The service is launched via the `__main__.py` entry point:

```python title="src/my_sensor/__main__.py"
import pydase
from my_sensor.my_sensor import MySensor

pydase.Server(MySensor()).run()
```

You can now start the service with:

```bash
python -m my_sensor
```

This approach ensures the service is fully configured via the `config.yaml` file,
separating service logic from configuration.
