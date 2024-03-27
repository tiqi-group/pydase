import logging
import time
from typing import TYPE_CHECKING, TypedDict

import socketio  # type: ignore

from pydase.client.proxy_class_factory import ProxyClassFactory
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.serializer import SerializedObject

if TYPE_CHECKING:
    from pydase.client.proxy_class_factory import ProxyClass

logger = logging.getLogger(__name__)


class NotifyDataDict(TypedDict):
    full_access_path: str
    value: SerializedObject


class NotifyDict(TypedDict):
    data: NotifyDataDict


class Client:
    def __init__(self, hostname: str, port: int):
        self.sio = socketio.Client()
        self.setup_events()
        self.proxy_class_factory = ProxyClassFactory(self.sio)
        self.proxy: ProxyClass | None = None
        self.sio.connect(
            f"ws://{hostname}:{port}",
            socketio_path="/ws/socket.io",
            transports=["websocket"],
        )
        while self.proxy is None:
            time.sleep(0.01)

    def setup_events(self) -> None:
        # TODO: subscribe to update event and update the cache of the proxy class.
        @self.sio.event
        def class_structure(data: SerializedObject) -> None:
            self.proxy = self.proxy_class_factory.create_proxy(data)

        @self.sio.event
        def notify(data: NotifyDict) -> None:
            if self.proxy is not None:
                self.proxy._notify_changed(
                    data["data"]["full_access_path"], loads(data["data"]["value"])
                )

    def disconnect(self) -> None:
        self.sio.disconnect()
