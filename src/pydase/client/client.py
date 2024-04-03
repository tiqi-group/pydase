import asyncio
import logging
import threading
from typing import Any, TypedDict, cast

import socketio  # type: ignore

import pydase.data_service
from pydase.client.proxy_class_factory import ProxyClassFactory, ProxyConnection
from pydase.utils.helpers import is_property_attribute
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.serializer import SerializedObject, dump
from pydase.utils.serialization.types import SerializedDataService

logger = logging.getLogger(__name__)


class NotifyDataDict(TypedDict):
    full_access_path: str
    value: SerializedObject


class NotifyDict(TypedDict):
    data: NotifyDataDict


class Client(pydase.data_service.DataService):
    def __init__(self, hostname: str, port: int):
        super().__init__()
        self._hostname = hostname
        self._port = port
        self._sio = socketio.AsyncClient()
        self._loop = asyncio.new_event_loop()
        self._proxy_class_factory = ProxyClassFactory(self._sio, self._loop)
        self._thread = threading.Thread(
            target=self.__asyncio_loop_thread, args=(self._loop,), daemon=True
        )
        self._thread.start()
        self.proxy: ProxyConnection
        asyncio.run_coroutine_threadsafe(self._connect(), self._loop).result()

    async def _connect(self) -> None:
        logger.debug("Connecting to server '%s:%s' ...", self._hostname, self._port)
        await self._setup_events()
        await self._sio.connect(
            f"ws://{self._hostname}:{self._port}",
            socketio_path="/ws/socket.io",
            transports=["websocket"],
        )

    def __asyncio_loop_thread(self, loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def _setup_events(self) -> None:
        @self._sio.event
        async def connect() -> None:
            logger.debug("Connected to '%s:%s' ...", self._hostname, self._port)
            serialized_data = cast(
                SerializedDataService, await self._sio.call("service_serialization")
            )
            if not hasattr(self, "proxy"):
                self.proxy = self._proxy_class_factory.create_proxy(serialized_data)
            else:
                # need to change to avoid overwriting the proxy class
                serialized_data["type"] = "DeviceConnection"
                super(pydase.DataService, self.proxy)._notify_changed(
                    "", loads(serialized_data)
                )
            self.proxy._connected = True

        @self._sio.event
        async def disconnect() -> None:
            logger.debug("Disconnected")
            self.proxy._connected = False

        @self._sio.event
        async def notify(data: NotifyDict) -> None:
            # Notify the DataServiceObserver directly, not going through
            # self._notify_changed as this would trigger the "update_value" event
            super(pydase.DataService, self.proxy)._notify_changed(
                data["data"]["full_access_path"],
                loads(data["data"]["value"]),
            )

    async def _disconnect(self) -> None:
        await self._sio.disconnect()

    def _notify_changed(self, changed_attribute: str, value: Any) -> None:
        if (
            changed_attribute.startswith("proxy.")
            # do not emit update event for properties which emit that event themselves
            and not is_property_attribute(self, changed_attribute)
            and all(part[0] != "_" for part in changed_attribute.split("."))
        ):

            async def update_value() -> None:
                await self._sio.call(
                    "update_value",
                    {
                        "access_path": changed_attribute[6:],
                        "value": dump(value),
                    },
                )

            asyncio.run_coroutine_threadsafe(update_value(), loop=self._loop)
        return super()._notify_changed(changed_attribute, value)
