import asyncio

import pydase.data_service
import pydase.task.decorator


class DeviceConnection(pydase.data_service.DataService):
    """
    Base class for device connection management within the pydase framework.

    This class serves as the foundation for subclasses that manage connections to
    specific devices. It implements automatic reconnection logic that periodically
    checks the device's availability and attempts to reconnect if the connection is
    lost. The frequency of these checks is controlled by the `_reconnection_wait_time`
    attribute.

    Subclassing
    -----------
    Users should primarily override the `connect` method to establish a connection
    to the device. This method should update the `self._connected` attribute to reflect
    the connection status:

    ```python
    class MyDeviceConnection(DeviceConnection):
        def connect(self) -> None:
            # Implementation to connect to the device
            # Update self._connected to `True` if connection is successful,
            # `False` otherwise
            ...
    ```

    Optionally, if additional logic is needed to determine the connection status,
    the `connected` property can also be overridden:

    ```python
    class MyDeviceConnection(DeviceConnection):
        @property
        def connected(self) -> bool:
            # Custom logic to determine connection status
            return some_custom_condition

    ```

    Frontend Representation
    -----------------------
    In the frontend, this class is represented without directly exposing the `connect`
    method and `connected` attribute. Instead, user-defined attributes, methods, and
    properties are displayed. When `self.connected` is `False`, the frontend component
    shows an overlay that allows manual triggering of the `connect()` method. This
    overlay disappears once the connection is successfully re-established.
    """

    def __init__(self) -> None:
        super().__init__()
        self._connected = False
        self._reconnection_wait_time = 10.0

    def connect(self) -> None:
        """Tries connecting to the device and changes `self._connected` status
        accordingly. This method is called every `self._reconnection_wait_time` seconds
        when `self.connected` is False. Users should override this method to implement
        device-specific connection logic.
        """

    @property
    def connected(self) -> bool:
        """Indicates if the device is currently connected or was recently connected.
        Users may override this property to incorporate custom logic for determining
        the connection status.
        """
        return self._connected

    @pydase.task.decorator.task(autostart=True)
    async def _handle_connection(self) -> None:
        """Automatically tries reconnecting to the device if it is not connected.
        This method leverages the `connect` method and the `connected` property to
        manage the connection status.
        """
        while True:
            if not self.connected:
                self.connect()
            await asyncio.sleep(self._reconnection_wait_time)
