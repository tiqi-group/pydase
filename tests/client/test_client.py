import threading
import time
from collections.abc import Generator
from typing import Any

import pydase
import pytest
from pydase.client.proxy_loader import ProxyAttributeError


@pytest.fixture(scope="session")
def pydase_server() -> Generator[pydase.Server, None, Any]:
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

        def my_method(self, input_str: str) -> str:
            return input_str

    server = pydase.Server(MyService(), web_port=9999)
    thread = threading.Thread(target=server.run)
    thread.start()
    time.sleep(0.1)  # Wait for the server to start

    yield server

    server.handle_exit()
    thread.join()


def test_property(pydase_server: pydase.Server) -> None:
    client = pydase.Client(port=9999)

    assert client.proxy.my_property == 12.1
    client.proxy.my_property = 2.1
    assert client.proxy.my_property == 2.1


def test_readonly_property(pydase_server: pydase.Server) -> None:
    client = pydase.Client(port=9999)

    assert client.proxy.name == "MyService"
    with pytest.raises(ProxyAttributeError):
        client.proxy.name = "Hello"


def test_method_execution(pydase_server: pydase.Server) -> None:
    client = pydase.Client(port=9999)

    assert client.proxy.my_method("My return string") == "My return string"
    assert client.proxy.my_method(input_str="My return string") == "My return string"

    with pytest.raises(TypeError):
        client.proxy.my_method("Something", 2)

    with pytest.raises(TypeError):
        client.proxy.my_method(kwarg="hello")
