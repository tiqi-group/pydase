import asyncio
import os
import signal
import threading
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from types import FrameType
from typing import Any, Optional

import uvicorn
from loguru import logger
from rpyc import (
    ForkingServer,  # can be used for multiprocessing, E.g. a database interface server
)
from rpyc import ThreadedServer
from uvicorn.server import HANDLED_SIGNALS

from pyDataService import DataService
from pyDataService.version import __version__

from .web_server import WebAPI

try:
    import tiqi_rpc
except ImportError:
    logger.debug("tiqi_rpc is not installed. tiqi_rpc server will not be exposed.")
    tiqi_rpc = None  # type: ignore


class Server:
    def __init__(  # noqa: CFQ002
        self,
        service: DataService,
        host: str = "0.0.0.0",
        rpc_port: int = 18871,
        tiqi_rpc_port: int = 6007,
        web_port: int = 8001,
        enable_rpc: bool = True,
        enable_tiqi_rpc: bool = True,
        enable_web: bool = True,
        use_forking_server: bool = False,
        web_settings: dict[str, Any] = {},
        **kwargs: Any,
    ) -> None:
        self._service = service
        self._host = host
        self._rpc_port = rpc_port
        self._tiqi_rpc_port = tiqi_rpc_port
        self._web_port = web_port
        self._enable_rpc = enable_rpc
        self._enable_tiqi_rpc = enable_tiqi_rpc
        self._enable_web = enable_web
        self._web_settings = web_settings
        self._kwargs = kwargs
        self._loop: asyncio.AbstractEventLoop
        self._rpc_server_type = ForkingServer if use_forking_server else ThreadedServer
        self.should_exit = False
        self.servers: dict[str, asyncio.Future[Any]] = {}
        self.executor: ThreadPoolExecutor | None = None
        self._info: dict[str, Any] = {
            "name": self._service.get_service_name(),
            "version": __version__,
            "rpc_port": self._rpc_port,
            "tiqi_rpc_port": self._tiqi_rpc_port,
            "web_port": self._web_port,
            "enable_rpc": self._enable_rpc,
            "enable_tiqi_rpc": self._enable_tiqi_rpc,
            "enable_web": self._enable_web,
            "web_settings": self._web_settings,
            **kwargs,
        }

    def run(self) -> None:
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

        logger.info(f"Started server process [{process_id}]")

        await self.startup()
        if self.should_exit:
            return
        await self.main_loop()
        await self.shutdown()

        logger.info(f"Finished server process [{process_id}]")

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
        if self._enable_tiqi_rpc and tiqi_rpc is not None:
            tiqi_rpc_server = tiqi_rpc.Server(
                RPCInterface(self._service, info=self._info, **self._kwargs),
                host=self._host,
                port=self._rpc_port,
            )
            tiqi_rpc_server.install_signal_handlers = lambda: None  # type: ignore
            future_or_task = self._loop.create_task(tiqi_rpc_server.serve())
            self.servers["tiqi-rpc"] = future_or_task
        if self._enable_web:
            self._wapi: WebAPI = WebAPI(
                service=self._service,
                info=self._info,
                **self._kwargs,
            )
            web_server = uvicorn.Server(
                uvicorn.Config(
                    self._wapi.fastapi_app, host=self._host, port=self._web_port
                )
            )

            def sio_callback(parent_path: str, name: str, value: Any) -> None:
                # TODO: an error happens when an attribute is set to a list
                # >   File "/usr/lib64/python3.11/json/encoder.py", line 180, in default
                # >       raise TypeError(f'Object of type {o.__class__.__name__} '
                # > TypeError: Object of type list is not JSON serializable
                async def notify() -> None:
                    try:
                        await self._wapi.sio.emit(  # type: ignore
                            "notify",
                            {
                                "data": {
                                    "parent_path": parent_path,
                                    "name": name,
                                    "value": value.name
                                    if isinstance(
                                        value, Enum
                                    )  # enums are not JSON serializable
                                    else value,
                                }
                            },
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send notification: {e}")

                self._loop.create_task(notify())

            self._service._callback_manager.add_notification_callback(sio_callback)

            # overwrite uvicorn's signal handlers, otherwise it will bogart SIGINT and
            # SIGTERM, which makes it impossible to escape out of
            web_server.install_signal_handlers = lambda: None  # type: ignore
            future_or_task = self._loop.create_task(web_server.serve())
            self.servers["web"] = future_or_task

    async def main_loop(self) -> None:
        while not self.should_exit:
            await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        logger.info("Shutting down")

        logger.info(f"Saving data to {self._service._filename}.")
        if self._service._filename is not None:
            self._service.write_to_file()

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
                logger.debug(f"Cancelled {server_name} server.")
            except Exception as e:
                logger.warning(f"Unexpected exception: {e}.")

    async def __cancel_tasks(self) -> None:
        for task in asyncio.all_tasks(self._loop):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug(f"Cancelled task {task.get_coro()}.")
            except Exception as e:
                logger.warning(f"Unexpected exception: {e}.")

    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        try:
            for sig in HANDLED_SIGNALS:
                self._loop.add_signal_handler(sig, self.handle_exit, sig, None)
        except NotImplementedError:  # pragma: no cover
            # Windows
            for sig in HANDLED_SIGNALS:
                signal.signal(sig, self.handle_exit)

    def handle_exit(self, sig: int = 0, frame: Optional[FrameType] = None) -> None:
        logger.info("Handling exit")
        if self.should_exit and sig == signal.SIGINT:
            self.force_exit = True
        else:
            self.should_exit = True

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
                    await self._wapi.sio.emit(  # type: ignore
                        "exception",
                        {
                            "data": {
                                "exception": str(exc),
                                "type": exc.__class__.__name__,
                            }
                        },
                    )

                loop.create_task(emit_exception())
        else:
            self.handle_exit()
