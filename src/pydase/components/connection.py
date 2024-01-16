import asyncio
from abc import ABC, abstractmethod

import pydase


class DeviceConnection(pydase.DataService, ABC):
    def __init__(self) -> None:
        super().__init__()
        self._autostart_tasks = {"_handle_connection": ()}  # type: ignore
        self._handle_connection_wait_time = 2.0

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
