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
    def __init__(
        self, sio_client: socketio.AsyncClient, loop: asyncio.AbstractEventLoop
    ) -> None:
        ProxyClassMixin.__init__(self)
        pydase.components.DeviceConnection.__init__(self)
        self._initialise(sio_client=sio_client, loop=loop)


class Client:
    """
    Args:
        hostname: str
            Hostname of the exposed service this client attempts to connect to.
            Default: "localhost"
        port: int
            Port of the exposed service this client attempts to connect on.
            Default: 8001
        blocking: bool
            If the constructor should wait until the connection to the service has been
            established. Default: True
    """

    def __init__(
        self, hostname: str = "localhost", port: int = 8001, blocking: bool = True
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
        if blocking:
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
        @self._sio.event
        async def connect() -> None:
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

        @self._sio.event
        async def disconnect() -> None:
            logger.debug("Disconnected from '%s:%s' ...", self._hostname, self._port)
            self.proxy._connected = False

        @self._sio.event
        async def notify(data: NotifyDict) -> None:
            self.proxy._notify_changed(
                data["data"]["full_access_path"],
                loads(data["data"]["value"]),
            )
