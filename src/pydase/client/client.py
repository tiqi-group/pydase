import asyncio
import logging
import sys
import threading
import urllib.parse
from types import TracebackType
from typing import TYPE_CHECKING, Any, TypedDict, cast

import socketio  # type: ignore

from pydase.client.proxy_class import ProxyClass
from pydase.client.proxy_loader import ProxyLoader
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.types import SerializedDataService, SerializedObject

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


logger = logging.getLogger(__name__)


class NotifyDataDict(TypedDict):
    full_access_path: str
    value: SerializedObject


class NotifyDict(TypedDict):
    data: NotifyDataDict


def asyncio_loop_thread(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


class Client:
    """
    A client for connecting to a remote pydase service using socket.io. This client
    handles asynchronous communication with a service, manages events such as
    connection, disconnection, and updates, and ensures that the proxy object is
    up-to-date with the server state.

    Args:
        url:
            The URL of the pydase Socket.IO server. This should always contain the
            protocol and the hostname.
        block_until_connected:
            If set to True, the constructor will block until the connection to the
            service has been established. This is useful for ensuring the client is
            ready to use immediately after instantiation. Default is True.
        sio_client_kwargs:
            Additional keyword arguments passed to the underlying
            [`AsyncClient`][socketio.AsyncClient]. This allows fine-tuning of the
            client's behaviour (e.g., reconnection attempts or reconnection delay).
            Default is an empty dictionary.
        client_id: Client identification that will be shown in the server logs this
            client is connecting to. This ID is passed as a `X-Client-Id` header in the
            HTTP(s) request. Defaults to None.

    Example:
        The following example demonstrates a `Client` instance that connects to another
        pydase service, while customising some of the connection settings for the
        underlying [`AsyncClient`][socketio.AsyncClient].

        ```python
        pydase.Client(url="ws://localhost:8001", sio_client_kwargs={
            "reconnection_attempts": 2,
            "reconnection_delay": 2,
            "reconnection_delay_max": 8,
        })
        ```

        When connecting to a server over a secure connection (i.e., the server is using
        SSL/TLS encryption), make sure that the `wss` protocol is used instead of `ws`:

        ```python
        pydase.Client(url="wss://my-service.example.com")
        ```
    """

    def __init__(
        self,
        *,
        url: str,
        block_until_connected: bool = True,
        sio_client_kwargs: dict[str, Any] = {},
        client_id: str | None = None,
    ):
        # Parse the URL to separate base URL and path prefix
        parsed_url = urllib.parse.urlparse(url)

        # Construct the base URL without the path
        self._base_url = urllib.parse.urlunparse(
            (parsed_url.scheme, parsed_url.netloc, "", "", "", "")
        )

        # Store the path prefix (e.g., "/service" in "ws://localhost:8081/service")
        self._path_prefix = parsed_url.path.rstrip("/")  # Remove trailing slash if any
        self._url = url
        self._sio = socketio.AsyncClient(**sio_client_kwargs)
        self._loop = asyncio.new_event_loop()
        self._client_id = client_id
        self.proxy = ProxyClass(
            sio_client=self._sio, loop=self._loop, reconnect=self.connect
        )
        """A proxy object representing the remote service, facilitating interaction as
        if it were local."""
        self._thread = threading.Thread(
            target=asyncio_loop_thread, args=(self._loop,), daemon=True
        )
        self._thread.start()
        self.connect(block_until_connected=block_until_connected)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.disconnect()

    def connect(self, block_until_connected: bool = True) -> None:
        connection_future = asyncio.run_coroutine_threadsafe(
            self._connect(), self._loop
        )
        if block_until_connected:
            connection_future.result()

    def disconnect(self) -> None:
        connection_future = asyncio.run_coroutine_threadsafe(
            self._disconnect(), self._loop
        )
        connection_future.result()

    async def _connect(self) -> None:
        logger.debug("Connecting to server '%s' ...", self._url)
        await self._setup_events()

        headers = {}
        if self._client_id is not None:
            headers["X-Client-Id"] = self._client_id

        await self._sio.connect(
            url=self._base_url,
            headers=headers,
            socketio_path=f"{self._path_prefix}/ws/socket.io",
            transports=["websocket"],
            retry=True,
        )

    async def _disconnect(self) -> None:
        await self._sio.disconnect()

    async def _setup_events(self) -> None:
        self._sio.on("connect", self._handle_connect)
        self._sio.on("disconnect", self._handle_disconnect)
        self._sio.on("notify", self._handle_update)

    async def _handle_connect(self) -> None:
        logger.debug("Connected to '%s' ...", self._url)
        serialized_object = cast(
            SerializedDataService, await self._sio.call("service_serialization")
        )
        ProxyLoader.update_data_service_proxy(
            self.proxy, serialized_object=serialized_object
        )
        serialized_object["type"] = "DeviceConnection"
        if self.proxy._service_representation is not None:
            # need to use object.__setattr__ to not trigger an observer notification
            object.__setattr__(self.proxy, "_service_representation", serialized_object)

            if TYPE_CHECKING:
                self.proxy._service_representation = serialized_object  # type: ignore
        self.proxy._notify_changed("", self.proxy)
        self.proxy._connected = True

    async def _handle_disconnect(self) -> None:
        logger.debug("Disconnected from '%s' ...", self._url)
        self.proxy._connected = False

    async def _handle_update(self, data: NotifyDict) -> None:
        self.proxy._notify_changed(
            data["data"]["full_access_path"],
            loads(data["data"]["value"]),
        )
