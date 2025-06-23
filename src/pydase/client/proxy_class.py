import asyncio
import logging
from collections.abc import Callable
from copy import deepcopy
from typing import TYPE_CHECKING, cast

import socketio  # type: ignore

import pydase.components
from pydase.client.proxy_loader import ProxyClassMixin
from pydase.utils.helpers import get_attribute_doc
from pydase.utils.serialization.types import SerializedDataService, SerializedObject

logger = logging.getLogger(__name__)


class ProxyClass(ProxyClassMixin, pydase.components.DeviceConnection):
    """
    A proxy class that serves as the interface for interacting with device connections
    via a socket.io client in an asyncio environment.

    Args:
        sio_client:
            The socket.io client instance used for asynchronous communication with the
            pydase service server.
        loop:
            The event loop in which the client operations are managed and executed.
        reconnect:
            The method that is called periodically when the client is not connected.

    This class is used to create a proxy object that behaves like a local representation
    of a remote pydase service, facilitating direct interaction as if it were local
    while actually communicating over network protocols.
    It can also be used as an attribute of a pydase service itself, e.g.

    ```python
    import pydase


    class MyService(pydase.DataService):
        proxy = pydase.Client(
            hostname="...", port=8001, block_until_connected=False
        ).proxy


    if __name__ == "__main__":
        service = MyService()
        server = pydase.Server(service, web_port=8002).run()
    ```
    """

    def __init__(
        self,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
        reconnect: Callable[..., None],
    ) -> None:
        if TYPE_CHECKING:
            self._service_representation: None | SerializedObject = None

        super().__init__()
        pydase.components.DeviceConnection.__init__(self)
        self._initialise(sio_client=sio_client, loop=loop)
        object.__setattr__(self, "_service_representation", None)
        self.reconnect = reconnect

    def serialize(self) -> SerializedObject:
        current_loop = asyncio.get_event_loop()

        if not self.connected or current_loop == self._loop:
            logger.debug(
                "Client not connected, or called from within client event loop - using "
                "fallback serialization"
            )
            if self._service_representation is None:
                serialized_service = pydase.components.DeviceConnection().serialize()
            else:
                serialized_service = self._service_representation

        else:
            future = cast(
                "asyncio.Future[SerializedDataService]",
                asyncio.run_coroutine_threadsafe(
                    self._sio.call("service_serialization"), self._loop
                ),
            )
            result = future.result()
            # need to use object.__setattr__ to not trigger an observer notification
            object.__setattr__(self, "_service_representation", result)
            if TYPE_CHECKING:
                self._service_representation = result
            serialized_service = result

        device_connection_value = cast(
            "dict[str, SerializedObject]",
            pydase.components.DeviceConnection().serialize()["value"],
        )

        readonly = False
        doc = get_attribute_doc(self)
        obj_name = self.__class__.__name__

        value = {
            **cast(
                "dict[str, SerializedObject]",
                # need to deepcopy to not overwrite the _service_representation dict
                # when adding a prefix with add_prefix_to_full_access_path
                deepcopy(serialized_service["value"]),
            ),
            **device_connection_value,
        }

        return {
            "full_access_path": "",
            "name": obj_name,
            "type": "DeviceConnection",
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }

    def connect(self) -> None:
        if not self._sio.reconnection or self._sio.reconnection_attempts > 0:
            self.reconnect(block_until_connected=False)
