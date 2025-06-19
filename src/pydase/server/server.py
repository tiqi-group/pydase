import asyncio
import logging
import os
import signal
import sys
import threading
from pathlib import Path
from types import FrameType
from typing import Any, Protocol, TypedDict

from pydase import DataService
from pydase.config import ServiceConfig
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.server.web_server import WebServer
from pydase.task.autostart import autostart_service_tasks

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)
if sys.platform == "win32":  # pragma: py-not-win32
    HANDLED_SIGNALS += (signal.SIGBREAK,)  # Windows signal 21. Sent by Ctrl+Break.

logger = logging.getLogger(__name__)


class AdditionalServerProtocol(Protocol):
    """
    A Protocol that defines the interface for additional servers.

    This protocol sets the standard for how additional servers should be implemented
    to ensure compatibility with the main Server class. The protocol requires that
    any server implementing it should have an __init__ method for initialization and a
    serve method for starting the server.

    Args:
        data_service_observer:
            Observer for the DataService, handling state updates and communication to
            connected clients through injected callbacks. Can be utilized to access the
            service and state manager, and to add custom state-update callbacks.
        host:
            Hostname or IP address where the server is accessible. Commonly '0.0.0.0' to
            bind to all network interfaces.
        port:
            Port number on which the server listens. Typically in the range 1024-65535
            (non-standard ports).
        **kwargs:
            Any additional parameters required for initializing the server. These
            parameters are specific to the server's implementation.
    """

    def __init__(
        self,
        data_service_observer: DataServiceObserver,
        host: str,
        port: int,
        **kwargs: Any,
    ) -> None: ...

    async def serve(self) -> Any:
        """Starts the server. This method should be implemented as an asynchronous
        method, which means that it should be able to run concurrently with other tasks.
        """


class AdditionalServer(TypedDict):
    """A TypedDict that represents the configuration for an additional server to be run
    alongside the main server.
    """

    server: type[AdditionalServerProtocol]
    """Server adhering to the
    [`AdditionalServerProtocol`][pydase.server.server.AdditionalServerProtocol]."""
    port: int
    """Port on which the server should run."""
    kwargs: dict[str, Any]
    """Additional keyword arguments that will be passed to the server's constructor """


class Server:
    """
    The `Server` class provides a flexible server implementation for the `DataService`.

    Args:
        service: The DataService instance that this server will manage.
        host: The host address for the server. Defaults to `'0.0.0.0'`, which means all
            available network interfaces.
        web_port: The port number for the web server. If set to None, it will use the
            port defined in
            [`ServiceConfig().web_port`][pydase.config.ServiceConfig.web_port]. Defaults
            to None.
        enable_web: Whether to enable the web server.
        filename: Filename of the file managing the service state persistence.
        additional_servers: A list of additional servers to run alongside the main
            server.
            Here's an example of how you might define an additional server:

            ```python
            class MyCustomServer:
                def __init__(
                    self,
                    data_service_observer: DataServiceObserver,
                    host: str,
                    port: int,
                    **kwargs: Any,
                ) -> None:
                    self.observer = data_service_observer
                    self.state_manager = self.observer.state_manager
                    self.service = self.state_manager.service
                    self.port = port
                    self.host = host
                    # handle any additional arguments...

                async def serve(self):
                    # code to start the server...
            ```

            And here's how you might add it to the `additional_servers` list when
            creating a `Server` instance:

            ```python
            server = Server(
                service=my_data_service,
                additional_servers=[
                    {
                        "server": MyCustomServer,
                        "port": 12345,
                        "kwargs": {"some_arg": "some_value"}
                    }
                ],
            )
            server.run()
            ```
        autosave_interval: Interval in seconds between automatic state save events.
            If set to `None`, automatic saving is disabled. Defaults to 30 seconds.
        **kwargs: Additional keyword arguments.

    # Advanced
    - [`post_startup`][pydase.Server.post_startup] hook:

          This method is intended to be overridden in subclasses. It runs immediately
          after all servers (web and additional) are initialized and before entering the
          main event loop. You can use this hook to register custom logic after the
          server is fully started.
    """

    def __init__(  # noqa: PLR0913
        self,
        service: DataService,
        host: str = "0.0.0.0",
        web_port: int | None = None,
        enable_web: bool = True,
        filename: str | Path | None = None,
        additional_servers: list[AdditionalServer] | None = None,
        autosave_interval: float = 30.0,
        **kwargs: Any,
    ) -> None:
        if additional_servers is None:
            additional_servers = []
        self._service = service
        self._host = host
        if web_port is None:
            self._web_port = ServiceConfig().web_port
        else:
            self._web_port = web_port
        self._enable_web = enable_web
        self._kwargs = kwargs
        self._additional_servers = additional_servers
        self.should_exit = False
        self.servers: dict[str, asyncio.Future[Any]] = {}

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._state_manager = StateManager(
            service=self._service,
            filename=filename,
            autosave_interval=autosave_interval,
        )
        self._observer = DataServiceObserver(self._state_manager)
        self._state_manager.load_state()
        autostart_service_tasks(self._service)

        self._web_server = WebServer(
            data_service_observer=self._observer,
            host=self._host,
            port=self._web_port,
            enable_frontend=self._enable_web,
            **self._kwargs,
        )

    def run(self) -> None:
        """
        Initializes the asyncio event loop and starts the server.

        This method should be called to start the server after it's been instantiated.
        """
        try:
            self._loop.run_until_complete(self.serve())
        finally:
            self._loop.close()

    async def serve(self) -> None:
        process_id = os.getpid()

        logger.info("Started server process [%s]", process_id)

        await self.startup()
        await self.post_startup()
        if self.should_exit:
            return
        await self.main_loop()
        await self.shutdown()

        logger.info("Finished server process [%s]", process_id)

    async def startup(self) -> None:
        self._loop.set_exception_handler(self.custom_exception_handler)
        self.install_signal_handlers()

        server_task = self._loop.create_task(self._web_server.serve())
        server_task.add_done_callback(self._handle_server_shutdown)
        self.servers["web"] = server_task

        for server in self._additional_servers:
            addin_server = server["server"](
                data_service_observer=self._observer,
                host=self._host,
                port=server["port"],
                **server["kwargs"],
            )

            server_name = (
                addin_server.__module__ + "." + addin_server.__class__.__name__
            )

            server_task = self._loop.create_task(addin_server.serve())
            server_task.add_done_callback(self._handle_server_shutdown)
            self.servers[server_name] = server_task

        self._loop.create_task(self._state_manager.autosave())

    def _handle_server_shutdown(self, task: asyncio.Task[Any]) -> None:
        """Handle server shutdown. If the service should exit, do nothing. Else, make
        the service exit."""

        if self.should_exit:
            return

        try:
            task.result()
        except Exception:
            self.should_exit = True

    async def main_loop(self) -> None:
        while not self.should_exit:
            await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        logger.info("Shutting down")

        logger.info("Saving data to %s.", self._state_manager.filename)
        self._state_manager.save_state()

        logger.debug("Cancelling servers")
        await self.__cancel_servers()
        logger.debug("Cancelling tasks")
        await self.__cancel_tasks()

    async def post_startup(self) -> None:
        """Override this in a subclass to register custom logic after startup."""

    async def __cancel_servers(self) -> None:
        for server_name, task in self.servers.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug("Cancelled '%s' server.", server_name)
            except Exception as e:
                logger.exception("Unexpected exception: %s", e)

    async def __cancel_tasks(self) -> None:
        for task in asyncio.all_tasks(self._loop):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug("Cancelled task '%s'.", task.get_coro())
            except Exception as e:
                logger.exception("Unexpected exception: %s", e)

    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        for sig in HANDLED_SIGNALS:
            signal.signal(sig, self.handle_exit)

    def handle_exit(self, sig: int = 0, frame: FrameType | None = None) -> None:
        if self.should_exit and sig == signal.SIGINT:
            logger.warning("Received signal '%s', forcing exit...", sig)
            os._exit(1)
        else:
            self.should_exit = True
            logger.warning(
                "Received signal '%s', exiting... (CTRL+C to force quit)", sig
            )

    def custom_exception_handler(
        self, loop: asyncio.AbstractEventLoop, context: dict[str, Any]
    ) -> None:
        # if any background task creates an unhandled exception, shut down the entire
        # loop. It's possible we don't want to do this, maybe make this optional in the
        # future
        loop.default_exception_handler(context)

        # here we exclude most kinds of exceptions from triggering this kind of shutdown
        exc = context.get("exception")
        if type(exc) not in [RuntimeError, KeyboardInterrupt, asyncio.CancelledError]:
            if loop.is_running():

                async def emit_exception() -> None:
                    try:
                        await self._web_server._sio.emit(
                            "exception",
                            {
                                "data": {
                                    "exception": str(exc),
                                    "type": exc.__class__.__name__,
                                }
                            },
                        )
                    except Exception as e:
                        logger.exception("Failed to send notification: %s", e)

                loop.create_task(emit_exception())
        else:
            self.handle_exit()
