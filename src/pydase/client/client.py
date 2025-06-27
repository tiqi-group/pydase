import asyncio
import logging
import socket
import sys
import threading
import urllib.parse
from builtins import ModuleNotFoundError
from types import TracebackType
from typing import TYPE_CHECKING, Any, TypedDict, cast

import aiohttp
import socketio  # type: ignore

from pydase.client.proxy_class import ProxyClass
from pydase.client.proxy_loader import (
    ProxyLoader,
    get_value,
    trigger_method,
    update_value,
)
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
    try:
        loop.run_forever()
    finally:
        loop.close()


class Client:
    """A client for connecting to a remote pydase service using Socket.IO. This client
    handles asynchronous communication with a service, manages events such as
    connection, disconnection, and updates, and ensures that the proxy object is
    up-to-date with the server state.

    Args:
        url: The URL of the pydase Socket.IO server. This should always contain the
            protocol (e.g., `ws` or `wss`) and the hostname, and can optionally include
            a path prefix (e.g., `ws://localhost:8001/service`).
        block_until_connected: If set to True, the constructor will block until the
            connection to the service has been established. This is useful for ensuring
            the client is ready to use immediately after instantiation. Default is True.
        sio_client_kwargs: Additional keyword arguments passed to the underlying
            [`AsyncClient`][socketio.AsyncClient]. This allows fine-tuning of the
            client's behaviour (e.g., reconnection attempts or reconnection delay).
        client_id: An optional client identifier. This ID is sent to the server as the
            `X-Client-Id` HTTP header. It can be used for logging or authentication
            purposes on the server side. If not provided, it defaults to the hostname
            of the machine running the client.
        proxy_url: An optional proxy URL to route the connection through. This is useful
            if the service is only reachable via an SSH tunnel or behind a firewall
            (e.g., `socks5://localhost:2222`).
        auto_update_proxy: If False, disables automatic updates from the server. Useful
            for request-only clients where real-time synchronization is not needed.

    Example:
        Connect to a service directly:

        ```python
        client = pydase.Client(url="ws://localhost:8001")
        ```

        Connect over a secure connection:

        ```python
        client = pydase.Client(url="wss://my-service.example.com")
        ```

        Connect using a SOCKS5 proxy (e.g., through an SSH tunnel):

        ```bash
        ssh -D 2222 user@gateway.example.com
        ```

        ```python
        client = pydase.Client(
            url="ws://remote-server:8001",
            proxy_url="socks5://localhost:2222"
        )
        ```
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        url: str,
        block_until_connected: bool = True,
        sio_client_kwargs: dict[str, Any] = {},
        client_id: str | None = None,
        proxy_url: str | None = None,
        auto_update_proxy: bool = True,  # new argument
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
        self._proxy_url = proxy_url
        self._client_id = client_id or socket.gethostname()
        self._sio_client_kwargs = sio_client_kwargs
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._auto_update_proxy = auto_update_proxy
        self.proxy: ProxyClass
        """A proxy object representing the remote service, facilitating interaction as
        if it were local."""
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
        if self._thread is None or self._loop is None:
            self._loop = self._initialize_loop_and_thread()
            self._initialize_socketio_client()
            self.proxy = ProxyClass(
                sio_client=self._sio,
                loop=self._loop,
                reconnect=self.connect,
            )

        connection_future = asyncio.run_coroutine_threadsafe(
            self._connect(), self._loop
        )
        if block_until_connected:
            connection_future.result()

    def _initialize_socketio_client(self) -> None:
        if self._proxy_url is not None:
            try:
                import aiohttp_socks.connector
            except ModuleNotFoundError:
                raise ModuleNotFoundError(
                    "Missing dependency 'aiohttp_socks'. To use SOCKS5 proxy support, "
                    "install the optional 'socks' extra:\n\n"
                    '    pip install "pydase[socks]"\n\n'
                    "This is required when specifying a `proxy_url` for "
                    "`pydase.Client`."
                )

            session = aiohttp.ClientSession(
                connector=aiohttp_socks.connector.ProxyConnector.from_url(
                    url=self._proxy_url, loop=self._loop
                ),
                loop=self._loop,
            )
            self._sio = socketio.AsyncClient(
                http_session=session, **self._sio_client_kwargs
            )
        else:
            self._sio = socketio.AsyncClient(**self._sio_client_kwargs)

    def _initialize_loop_and_thread(self) -> asyncio.AbstractEventLoop:
        """Initialize a new asyncio event loop, start it in a background thread,
        and create the ProxyClass instance bound to that loop.
        """

        loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=asyncio_loop_thread,
            args=(loop,),
            daemon=True,
        )
        self._thread.start()

        return loop

    def disconnect(self) -> None:
        if self._loop is not None and self._thread is not None:
            connection_future = asyncio.run_coroutine_threadsafe(
                self._disconnect(), self._loop
            )
            connection_future.result()

            # Stop the event loop and thread
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join()
            self._thread = None

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
        if self._auto_update_proxy:
            self._sio.on("notify", self._handle_update)

    async def _handle_connect(self) -> None:
        logger.debug("Connected to '%s' ...", self._url)
        if self._auto_update_proxy:
            serialized_object = cast(
                "SerializedDataService", await self._sio.call("service_serialization")
            )
            ProxyLoader.update_data_service_proxy(
                self.proxy, serialized_object=serialized_object
            )
            serialized_object["type"] = "DeviceConnection"
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

    def get_value(self, access_path: str) -> Any:
        """Retrieve the current value of a remote attribute.

        Args:
            access_path: The dot-separated path to the attribute in the remote service.

        Returns:
            The deserialized value of the remote attribute, or None if the client is not
            connected.

        Example:
            ```python
            value = client.get_value("my_device.temperature")
            print(value)
            ```
        """

        if self._loop is not None:
            return get_value(
                sio_client=self._sio,
                loop=self._loop,
                access_path=access_path,
            )
        return None

    def update_value(self, access_path: str, new_value: Any) -> Any:
        """Set a new value for a remote attribute.

        Args:
            access_path: The dot-separated path to the attribute in the remote service.
            new_value: The new value to assign to the attribute.

        Example:
            ```python
            client.update_value("my_device.power", True)
            ```
        """

        if self._loop is not None:
            update_value(
                sio_client=self._sio,
                loop=self._loop,
                access_path=access_path,
                value=new_value,
            )

    def trigger_method(self, access_path: str, *args: Any, **kwargs: Any) -> Any:
        """Trigger a remote method with optional arguments.

        Args:
            access_path: The dot-separated path to the method in the remote service.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            The return value of the method call, if any.

        Example:
            ```python
            result = client.trigger_method("my_device.calibrate", timeout=5)
            print(result)
            ```
        """

        if self._loop is not None:
            return trigger_method(
                sio_client=self._sio,
                loop=self._loop,
                access_path=access_path,
                args=list(args),
                kwargs=kwargs,
            )
        return None
