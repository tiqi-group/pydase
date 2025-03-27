# Logging in pydase

The `pydase` library organizes its loggers per module, mirroring the Python package hierarchy. This structured approach allows for granular control over logging levels and behaviour across different parts of the library. Logs can also include details about client identification based on headers sent by the client or proxy, providing additional context for debugging or auditing.

## Changing the pydase Log Level

You have two primary ways to adjust the log levels in `pydase`:

1. **Directly targeting `pydase` loggers**

     You can set the log level for any `pydase` logger directly in your code. This method is useful for fine-tuning logging levels for specific modules within `pydase`. For instance, if you want to change the log level of the main `pydase` logger or target a submodule like `pydase.data_service`, you can do so as follows:

    ```python
    # <your_script.py>
    import logging

    # Set the log level for the main pydase logger
    logging.getLogger("pydase").setLevel(logging.INFO)

    # Optionally, target a specific submodule logger
    # logging.getLogger("pydase.data_service").setLevel(logging.DEBUG)

    # Your logger for the current script
    from pydase.utils.logging import configure_logging_with_pydase_formatter
    configure_logging_with_pydase_formatter(level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.debug("My debug message.")
    ```

    This approach allows for specific control over different parts of the `pydase` library, depending on your logging needs.

2. **Using the `ENVIRONMENT` environment variable**

    For a more global setting that affects the entire `pydase` library, you can utilize the `ENVIRONMENT` environment variable. Setting this variable to `"production"` will configure all `pydase` loggers to only log messages of level `"INFO"` and above, filtering out more verbose logging. This is particularly useful for production environments where excessive logging can be overwhelming or unnecessary.

    ```bash
    ENVIRONMENT="production" python -m <module_using_pydase>
    ```

    In the absence of this setting, the default behavior is to log everything of level `"DEBUG"` and above, suitable for development environments where more detailed logs are beneficial.

## Client Identification in pydase Logs

The logging system in `pydase` includes information about clients based on headers sent by the client or a proxy. The priority for identifying the client is fixed and as follows:

1. **`Remote-User` Header**: This header is typically set by authentication servers like [Authelia](https://www.authelia.com/). While it can be set manually by users, its primary purpose is to provide client information authenticated through such servers.
2. **`X-Client-ID` Header**: This header is intended for use by Python clients to pass custom client identification information. It acts as a fallback when the `Remote-User` header is not available.
3. **Default Socket.IO Session ID**: If neither of the above headers is present, the system falls back to the default Socket.IO session ID to identify the client.

For example, a log entries might include the following details based on the available headers:

```plaintext
2025-01-20 06:47:50.940 | INFO     | pydase.server.web_server.api.v1.application:_get_value:36 - Client [id=This is me!] is getting the value of 'property_attr'

2025-01-20 06:48:13.710 | INFO     | pydase.server.web_server.api.v1.application:_get_value:36 - Client [user=Max Muster] is getting the value of 'property_attr'
```

## Configuring Logging in Services

To configure logging in services built with `pydase`, use the helper function [`configure_logging_with_pydase_formatter`][pydase.utils.logging.configure_logging_with_pydase_formatter]. This function sets up a logger with the same formatting used internally by `pydase`, so your service logs match the style and structure of `pydase` logs.

### Example

If your service follows a typical layout like:

```text
└── src
    └── my_service
        ├── __init__.py
        └── ...
```

you should call `configure_logging_with_pydase_formatter` inside `src/my_service/__init__.py`. This ensures the logger is configured as soon as your service is imported, and before any log messages are emitted.

```python title="src/my_service/__init__.py"
import sys
from pydase.utils.logging import configure_logging_with_pydase_formatter

configure_logging_with_pydase_formatter(
    name="my_service",      # Use the package/module name or None for the root logger
    level=logging.DEBUG,    # Set the desired logging level (defaults to INFO)
    stream=sys.stderr       # Optional: set the output stream (stderr by default)
)
```

### Notes

- If you pass `name=None`, the root logger will be configured. This affects **all logs** that propagate to the root logger.
- Passing a specific `name` like `"my_service"` allows you to scope the configuration to your service only, which is safer in multi-library environments.
- You can use `sys.stdout` instead of `sys.stderr` if your logs are being captured or processed differently (e.g., in containers or logging systems).
