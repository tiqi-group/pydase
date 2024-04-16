import asyncio
import logging
import threading
from typing import TypedDict, cast

import socketio  # type: ignore

import pydase.components
from pydase.client.proxy_loader import ProxyClassMixin, ProxyLoader
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.types import SerializedDataService, SerializedObject

logger = logging.getLogger(__name__)


class NotifyDataDict(TypedDict):
    full_access_path: str
    value: SerializedObject


class NotifyDict(TypedDict):
    data: NotifyDataDict


def asyncio_loop_thread(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


class ProxyClass(ProxyClassMixin, pydase.components.DeviceConnection):
    """
    A proxy class that serves as the interface for interacting with device connections
    via a socket.io client in an asyncio environment.

    Args:
        sio_client (socketio.AsyncClient):
            The socket.io client instance used for asynchronous communication with the
            pydase service server.
        loop (asyncio.AbstractEventLoop):
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
        self._initialise(sio_client=sio_client, loop=loop)


class Client:
    """
    A client for connecting to a remote pydase service using socket.io. This client
    handles asynchronous communication with a service, manages events such as
    connection, disconnection, and updates, and ensures that the proxy object is
    up-to-date with the server state.

    Attributes:
        proxy (ProxyClass):
            A proxy object representing the remote service, facilitating interaction as
            if it were local.

    Args:
        hostname (str):
            Hostname of the exposed service this client attempts to connect to.
            Default is "localhost".
        port (int):
            Port of the exposed service this client attempts to connect on.
            Default is 8001.
        block_until_connected (bool):
            If set to True, the constructor will block until the connection to the
            service has been established. This is useful for ensuring the client is
            ready to use immediately after instantiation. Default is True.
    """

    def __init__(
        self,
        hostname: str,
        port: int,
        block_until_connected: bool = True,
    ):
        self._hostname = hostname
        self._port = port
        self._sio = socketio.AsyncClient()
        self._loop = asyncio.new_event_loop()
        self.proxy = ProxyClass(sio_client=self._sio, loop=self._loop)
        self._thread = threading.Thread(
            target=asyncio_loop_thread, args=(self._loop,), daemon=True
        )
        self._thread.start()
        connection_future = asyncio.run_coroutine_threadsafe(
            self._connect(), self._loop
        )
        if block_until_connected:
            connection_future.result()

    async def _connect(self) -> None:
        logger.debug("Connecting to server '%s:%s' ...", self._hostname, self._port)
        await self._setup_events()
        await self._sio.connect(
            f"ws://{self._hostname}:{self._port}",
            socketio_path="/ws/socket.io",
            transports=["websocket"],
            retry=True,
        )

    async def _setup_events(self) -> None:
        self._sio.on("connect", self._handle_connect)
        self._sio.on("disconnect", self._handle_disconnect)
        self._sio.on("notify", self._handle_update)

    async def _handle_connect(self) -> None:
        logger.debug("Connected to '%s:%s' ...", self._hostname, self._port)
        serialized_object = cast(
            SerializedDataService, await self._sio.call("service_serialization")
        )
        ProxyLoader.update_data_service_proxy(
            self.proxy, serialized_object=serialized_object
        )
        serialized_object["type"] = "DeviceConnection"
        self.proxy._notify_changed("", loads(serialized_object))
        self.proxy._connected = True

    async def _handle_disconnect(self) -> None:
        logger.debug("Disconnected from '%s:%s' ...", self._hostname, self._port)
        self.proxy._connected = False

    async def _handle_update(self, data: NotifyDict) -> None:
        self.proxy._notify_changed(
            data["data"]["full_access_path"],
            loads(data["data"]["value"]),
        )
