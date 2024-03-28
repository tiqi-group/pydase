import logging
import time
from typing import Any, TypedDict

import socketio  # type: ignore

import pydase
from pydase.client.proxy_class_factory import ProxyClassFactory, ProxyConnection
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.serializer import SerializedObject, dump
from pydase.utils.serialization.types import SerializedDataService

logger = logging.getLogger(__name__)


class NotifyDataDict(TypedDict):
    full_access_path: str
    value: SerializedObject


class NotifyDict(TypedDict):
    data: NotifyDataDict


class Client(pydase.DataService):
    def __init__(self, hostname: str, port: int):
        super().__init__()
        self._sio = socketio.Client()
        self._setup_events()
        self._proxy_class_factory = ProxyClassFactory(self._sio)
        self.proxy = ProxyConnection()
        self._sio.connect(
            f"ws://{hostname}:{port}",
            socketio_path="/ws/socket.io",
            transports=["websocket"],
        )
        while not self.proxy._initialised:
            time.sleep(0.01)

    def _setup_events(self) -> None:
        @self._sio.event
        def class_structure(data: SerializedDataService) -> None:
            if not self.proxy._initialised:
                self.proxy = self._proxy_class_factory.create_proxy(data)
            else:
                # need to change to avoid overwriting the proxy class
                data["type"] = "DeviceConnection"
                super(pydase.DataService, self.proxy)._notify_changed("", loads(data))

        @self._sio.event
        def notify(data: NotifyDict) -> None:
            # Notify the DataServiceObserver directly, not going through
            # self._notify_changed as this would trigger the "update_value" event
            super(pydase.DataService, self.proxy)._notify_changed(
                data["data"]["full_access_path"],
                loads(data["data"]["value"]),
            )

    def disconnect(self) -> None:
        self._sio.disconnect()

    def _notify_changed(self, changed_attribute: str, value: Any) -> None:
        if (
            changed_attribute.startswith("proxy.")
            and all(part[0] != "_" for part in changed_attribute.split("."))
            and changed_attribute != "proxy.connected"
        ):
            logger.debug(f"{changed_attribute}: {value}")

            self._sio.call(
                "update_value",
                {
                    "access_path": changed_attribute[6:],
                    "value": dump(value),
                },
            )
        return super()._notify_changed(changed_attribute, value)
