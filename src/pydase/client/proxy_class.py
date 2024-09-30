import asyncio
import logging
from typing import cast

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
        self, sio_client: socketio.AsyncClient, loop: asyncio.AbstractEventLoop
    ) -> None:
        super().__init__()
        pydase.components.DeviceConnection.__init__(self)
        self._initialise(sio_client=sio_client, loop=loop)

    def serialize(self) -> SerializedObject:
        readonly = False
        doc = get_attribute_doc(self)
        obj_name = self.__class__.__name__
        serialization_future = cast(
            asyncio.Future[SerializedDataService],
            asyncio.run_coroutine_threadsafe(
                self._sio.call("service_serialization"), self._loop
            ),
        )
        value = serialization_future.result()["value"]

        return {
            "full_access_path": "",
            "name": obj_name,
            "type": "DeviceConnection",
            "value": value,
            "readonly": readonly,
            "doc": doc,
        }
