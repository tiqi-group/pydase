import logging
import time

import socketio  # type: ignore

from pydase.client.client_deserializer import ClientDeserializer
from pydase.utils.serializer import SerializedObject

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, hostname: str, port: int):
        self.sio = socketio.Client()
        self.setup_events()
        self.proxy = None
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
            ClientDeserializer._sio = self.sio
            self.proxy = ClientDeserializer.deserialize(data)

    def disconnect(self) -> None:
        self.sio.disconnect()
