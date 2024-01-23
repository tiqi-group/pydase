import asyncio
from abc import ABC, abstractmethod

import pydase


class DeviceConnection(pydase.DataService, ABC):
    """
    Abstract base class for device connection management in the pydase framework.

    This class forms the foundation for subclasses that manage connections to specific
    devices. Implementers are required to define the `connect()` method and the
    `connected` property. The `connect()` method should handle the logic to establish a
    connection with the device, while the `connected` property should return the current
    connection status.

    An instance of this class automatically starts a task that periodically checks the
    device's availability and attempts reconnection if necessary.

    In the frontend, this class is represented without directly exposing the `connect`
    method and `connected` attribute. Instead, it displays user-defined attributes,
    methods, and properties. When the device connection is not established, the frontend
    component is overlaid, allowing manual triggering of the `connect()` method. The
    overlay disappears once the connection is re-established.
    """

    def __init__(self) -> None:
        super().__init__()
        self._autostart_tasks["_handle_connection"] = ()  # type: ignore
        self._handle_connection_wait_time = 10.0

    @abstractmethod
    def connect(self) -> None:
        """Tries to connect to the abstracted device."""
        ...

    @property
    @abstractmethod
    def connected(self) -> bool:
        """Checks if the abstracted device is connected."""
        ...

    async def _handle_connection(self) -> None:
        """Tries reconnecting to the device if it is not connected."""
        while True:
            if not self.connected:
                self.connect()
            await asyncio.sleep(self._handle_connection_wait_time)
