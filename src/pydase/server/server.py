import asyncio
import logging
import os
import signal
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import FrameType
from typing import Any, Protocol, TypedDict

import uvicorn
from rpyc import ForkingServer, ThreadedServer  # type: ignore[import-untyped]
from uvicorn.server import HANDLED_SIGNALS

from pydase import DataService
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.utils.serializer import dump

from .web_server import WebAPI

logger = logging.getLogger(__name__)


class AdditionalServerProtocol(Protocol):
    """
    A Protocol that defines the interface for additional servers.

    This protocol sets the standard for how additional servers should be implemented
    to ensure compatibility with the main Server class. The protocol requires that
    any server implementing it should have an __init__ method for initialization and a
    serve method for starting the server.

    Parameters:
    -----------
    service: DataService
        The instance of DataService that the server will use. This could be the main
        application or a specific service that the server will provide.

    port: int
        The port number at which the server will be accessible. This should be a valid
        port number, typically in the range 1024-65535.

    host: str
        The hostname or IP address at which the server will be hosted. This could be a
        local address (like '127.0.0.1' for localhost) or a public IP address.

    state_manager: StateManager
        The state manager managing the state cache and persistence of the exposed
        service.

    **kwargs: Any
        Any additional parameters required for initializing the server. These parameters
        are specific to the server's implementation.
    """

    def __init__(
        self,
        service: DataService,
        port: int,
        host: str,
        state_manager: StateManager,
        **kwargs: Any,
    ) -> None:
        ...

    async def serve(self) -> Any:
        """Starts the server. This method should be implemented as an asynchronous
        method, which means that it should be able to run concurrently with other tasks.
        """


class AdditionalServer(TypedDict):
    """
    A TypedDict that represents the configuration for an additional server to be run
    alongside the main server.

    This class is used to specify the server type, the port on which the server should
    run, and any additional keyword arguments that should be passed to the server when
    it's instantiated.
    """

    server: type[AdditionalServerProtocol]
    port: int
    kwargs: dict[str, Any]


class Server:
    """
    The `Server` class provides a flexible server implementation for the `DataService`.

    Parameters:
    -----------
    service: DataService
        The DataService instance that this server will manage.
    host: str
        The host address for the server. Default is '0.0.0.0', which means all available
        network interfaces.
    rpc_port: int
        The port number for the RPC server. Default is 18871.
    web_port: int
        The port number for the web server. Default is 8001.
    enable_rpc: bool
        Whether to enable the RPC server. Default is True.
    enable_web: bool
        Whether to enable the web server. Default is True.
    filename: str | Path | None
        Filename of the file managing the service state persistence. Defaults to None.
    use_forking_server: bool
        Whether to use ForkingServer for multiprocessing. Default is False.
    additional_servers : list[AdditionalServer]
        A list of additional servers to run alongside the main server. Each entry in the
        list should be a dictionary with the following structure:

        - server: A class that adheres to the AdditionalServerProtocol. This class
            should have an `__init__` method that accepts the DataService instance,
            port, host, and optional keyword arguments, and a `serve` method that is a
            coroutine responsible for starting the server.
        - port: The port on which the additional server will be running.
        - kwargs: A dictionary containing additional keyword arguments that will be
            passed to the server's `__init__` method.

        Here's an example of how you might define an additional server:


        >>>     class MyCustomServer:
        ...         def __init__(
        ...             self,
        ...             service: DataService,
        ...             port: int,
        ...             host: str,
        ...             state_manager: StateManager,
        ...             **kwargs: Any
        ...         ):
        ...             self.service = service
        ...             self.state_manager = state_manager
        ...             self.port = port
        ...             self.host = host
        ...             # handle any additional arguments...
        ...
        ...         async def serve(self):
        ...             # code to start the server...

        And here's how you might add it to the `additional_servers` list when creating a
        `Server` instance:

        >>>    server = Server(
        ...        service=my_data_service,
        ...        additional_servers=[
        ...            {
        ...                "server": MyCustomServer,
        ...                "port": 12345,
        ...                "kwargs": {"some_arg": "some_value"}
        ...            }
        ...        ],
        ...    )
        ...    server.run()

    **kwargs: Any
        Additional keyword arguments.
    """

    def __init__(  # noqa: PLR0913
        self,
        service: DataService,
        host: str = "0.0.0.0",
        rpc_port: int = 18871,
        web_port: int = 8001,
        enable_rpc: bool = True,
        enable_web: bool = True,
        filename: str | Path | None = None,
        use_forking_server: bool = False,
        additional_servers: list[AdditionalServer] | None = None,
        **kwargs: Any,
    ) -> None:
        if additional_servers is None:
            additional_servers = []
        self._service = service
        self._host = host
        self._rpc_port = rpc_port
        self._web_port = web_port
        self._enable_rpc = enable_rpc
        self._enable_web = enable_web
        self._kwargs = kwargs
        self._loop: asyncio.AbstractEventLoop
        self._rpc_server_type = ForkingServer if use_forking_server else ThreadedServer
        self._additional_servers = additional_servers
        self.should_exit = False
        self.servers: dict[str, asyncio.Future[Any]] = {}
        self.executor: ThreadPoolExecutor | None = None
        self._state_manager = StateManager(self._service, filename)
        if getattr(self._service, "_filename", None) is not None:
            self._service._state_manager = self._state_manager
        self._state_manager.load_state()
        self._observer = DataServiceObserver(self._state_manager)

    def run(self) -> None:
        """
        Initializes the asyncio event loop and starts the server.

        This method should be called to start the server after it's been instantiated.

        Raises
        ------
        Exception
            If there's an error while running the server, the error will be propagated
            after the server is shut down.
        """
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self.serve())
        except Exception:
            self._loop.run_until_complete(self.shutdown())
            raise

    async def serve(self) -> None:
        process_id = os.getpid()

        logger.info("Started server process [%s]", process_id)

        await self.startup()
        if self.should_exit:
            return
        await self.main_loop()
        await self.shutdown()

        logger.info("Finished server process [%s]", process_id)

    async def startup(self) -> None:  # noqa: C901
        self._loop = asyncio.get_running_loop()
        self._loop.set_exception_handler(self.custom_exception_handler)
        self.install_signal_handlers()
        self._service._task_manager.start_autostart_tasks()

        if self._enable_rpc:
            self.executor = ThreadPoolExecutor()
            self._rpc_server = self._rpc_server_type(
                self._service,
                port=self._rpc_port,
                protocol_config={
                    "allow_all_attrs": True,
                    "allow_setattr": True,
                },
            )
            future_or_task = self._loop.run_in_executor(
                executor=self.executor, func=self._rpc_server.start
            )
            self.servers["rpyc"] = future_or_task
        for server in self._additional_servers:
            addin_server = server["server"](
                self._service,
                port=server["port"],
                host=self._host,
                state_manager=self._state_manager,
                **server["kwargs"],
            )

            server_name = (
                addin_server.__module__ + "." + addin_server.__class__.__name__
            )

            future_or_task = self._loop.create_task(addin_server.serve())
            self.servers[server_name] = future_or_task
        if self._enable_web:
            self._wapi = WebAPI(
                service=self._service,
                state_manager=self._state_manager,
                **self._kwargs,
            )
            web_server = uvicorn.Server(
                uvicorn.Config(
                    self._wapi.fastapi_app, host=self._host, port=self._web_port
                )
            )

            def sio_callback(
                full_access_path: str, value: Any, cached_value_dict: dict[str, Any]
            ) -> None:
                if cached_value_dict != {}:
                    serialized_value = dump(value)
                    if cached_value_dict["type"] != "method":
                        cached_value_dict["type"] = serialized_value["type"]

                    cached_value_dict["value"] = serialized_value["value"]

                    async def notify() -> None:
                        try:
                            await self._wapi.sio.emit(
                                "notify",
                                {
                                    "data": {
                                        "full_access_path": full_access_path,
                                        "value": cached_value_dict,
                                    }
                                },
                            )
                        except Exception as e:
                            logger.warning("Failed to send notification: %s", e)

                    self._loop.create_task(notify())

            self._observer.add_notification_callback(sio_callback)

            # overwrite uvicorn's signal handlers, otherwise it will bogart SIGINT and
            # SIGTERM, which makes it impossible to escape out of
            web_server.install_signal_handlers = lambda: None  # type: ignore[method-assign]
            future_or_task = self._loop.create_task(web_server.serve())
            self.servers["web"] = future_or_task

    async def main_loop(self) -> None:
        while not self.should_exit:
            await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        logger.info("Shutting down")

        logger.info("Saving data to %s.", self._state_manager.filename)
        if self._state_manager is not None:
            self._state_manager.save_state()

        await self.__cancel_servers()
        await self.__cancel_tasks()

        if hasattr(self, "_rpc_server") and self._enable_rpc:
            logger.debug("Closing rpyc server.")
            self._rpc_server.close()

    async def __cancel_servers(self) -> None:
        for server_name, task in self.servers.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug("Cancelled '%s' server.", server_name)
            except Exception as e:
                logger.warning("Unexpected exception: %s", e)

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
            if self._enable_web:

                async def emit_exception() -> None:
                    try:
                        await self._wapi.sio.emit(
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
