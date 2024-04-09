import threading
import time
from collections.abc import Generator
from typing import Any

import pydase
import pytest
from pydase.client.proxy_loader import ProxyAttributeError


@pytest.fixture(scope="session")
def pydase_client() -> Generator[pydase.Client, None, Any]:
    class SubService(pydase.DataService):
        name = "SubService"

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._name = "MyService"
            self._my_property = 12.1
            self.sub_service = SubService()

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
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    client = pydase.Client(port=9999)
    while not client.proxy.connected:
        time.sleep(0.001)  # Wait for the client to connect

    yield client

    server.handle_exit()
    thread.join()


def test_property(pydase_client: pydase.Client) -> None:
    assert pydase_client.proxy.my_property == 12.1
    pydase_client.proxy.my_property = 2.1
    assert pydase_client.proxy.my_property == 2.1


def test_readonly_property(pydase_client: pydase.Client) -> None:
    assert pydase_client.proxy.name == "MyService"
    with pytest.raises(ProxyAttributeError):
        pydase_client.proxy.name = "Hello"


def test_method_execution(pydase_client: pydase.Client) -> None:
    assert pydase_client.proxy.my_method("My return string") == "My return string"
    assert (
        pydase_client.proxy.my_method(input_str="My return string")
        == "My return string"
    )

    with pytest.raises(TypeError):
        pydase_client.proxy.my_method("Something", 2)

    with pytest.raises(TypeError):
        pydase_client.proxy.my_method(kwarg="hello")


def test_nested_service(pydase_client: pydase.Client) -> None:
    assert pydase_client.proxy.sub_service.name == "SubService"
    pydase_client.proxy.sub_service.name = "New name"
    assert pydase_client.proxy.sub_service.name == "New name"
