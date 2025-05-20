import threading
from collections.abc import Callable, Generator
from typing import Any

import pytest
import socketio.exceptions

import pydase


@pytest.fixture(scope="function")
def pydase_restartable_server() -> Generator[
    tuple[
        pydase.Server,
        threading.Thread,
        pydase.DataService,
        Callable[
            [pydase.Server, threading.Thread, pydase.DataService],
            tuple[pydase.Server, threading.Thread],
        ],
    ],
    None,
    Any,
]:
    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._name = "MyService"
            self._my_property = 12.1

        @property
        def my_property(self) -> float:
            return self._my_property

        @my_property.setter
        def my_property(self, value: float) -> None:
            self._my_property = value

        @property
        def name(self) -> str:
            return self._name

    service_instance = MyService()
    server = pydase.Server(service_instance, web_port=9999)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    def restart(
        server: pydase.Server,
        thread: threading.Thread,
        service_instance: pydase.DataService,
    ) -> tuple[pydase.Server, threading.Thread]:
        server.handle_exit()
        thread.join()

        server = pydase.Server(service_instance, web_port=9999)
        new_thread = threading.Thread(target=server.run, daemon=True)
        new_thread.start()

        return server, new_thread

    yield server, thread, service_instance, restart


def test_reconnection(
    pydase_restartable_server: tuple[
        pydase.Server,
        threading.Thread,
        pydase.DataService,
        Callable[
            [pydase.Server, threading.Thread, pydase.DataService],
            tuple[pydase.Server, threading.Thread],
        ],
    ],
) -> None:
    client = pydase.Client(
        url="ws://localhost:9999",
        sio_client_kwargs={
            "reconnection": False,
        },
    )
    client_2 = pydase.Client(
        url="ws://localhost:9999",
        sio_client_kwargs={
            "reconnection_attempts": 1,
        },
    )

    server, thread, service_instance, restart = pydase_restartable_server
    service_instance._name = "New service name"

    server, thread = restart(server, thread, service_instance)

    with pytest.raises(socketio.exceptions.BadNamespaceError):
        client.proxy.name
        client_2.proxy.name

    client.proxy.reconnect()
    client_2.proxy.reconnect()

    # the service proxies successfully reconnect and get the new service name
    assert client.proxy.name == "New service name"
    assert client_2.proxy.name == "New service name"

    server.handle_exit()
    thread.join()
