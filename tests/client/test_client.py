import threading
from collections.abc import Generator
from typing import Any

import pytest

import pydase
from pydase.client.proxy_loader import ProxyAttributeError


@pytest.fixture(scope="module")
def pydase_client() -> Generator[pydase.Client, None, Any]:
    class SubService(pydase.DataService):
        name = "SubService"

    subservice_instance = SubService()

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._name = "MyService"
            self._my_property = 12.1
            self.sub_service = SubService()
            self.list_attr = [1, 2]
            self.dict_attr = {
                "foo": subservice_instance,
                "dotted.key": subservice_instance,
            }

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

        async def my_async_method(self, input_str: str) -> str:
            return input_str

    server = pydase.Server(MyService(), web_port=9999)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    client = pydase.Client(url="ws://localhost:9999")

    yield client

    client.disconnect()
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


def test_async_method_execution(pydase_client: pydase.Client) -> None:
    assert pydase_client.proxy.my_async_method("My return string") == "My return string"
    assert (
        pydase_client.proxy.my_async_method(input_str="My return string")
        == "My return string"
    )


def test_nested_service(pydase_client: pydase.Client) -> None:
    assert pydase_client.proxy.sub_service.name == "SubService"
    pydase_client.proxy.sub_service.name = "New name"
    assert pydase_client.proxy.sub_service.name == "New name"


def test_list(pydase_client: pydase.Client) -> None:
    assert pydase_client.proxy.list_attr == [1, 2]

    pydase_client.proxy.list_attr.append(1)
    assert pydase_client.proxy.list_attr == [1, 2, 1]

    pydase_client.proxy.list_attr.extend([123, 2.1])
    assert pydase_client.proxy.list_attr == [1, 2, 1, 123, 2.1]

    pydase_client.proxy.list_attr.insert(1, 1.2)
    assert pydase_client.proxy.list_attr == [1, 1.2, 2, 1, 123, 2.1]

    assert pydase_client.proxy.list_attr.pop() == 2.1
    assert pydase_client.proxy.list_attr == [1, 1.2, 2, 1, 123]

    pydase_client.proxy.list_attr.remove(1.2)
    assert pydase_client.proxy.list_attr == [1, 2, 1, 123]

    pydase_client.proxy.list_attr[1] = 1337
    assert pydase_client.proxy.list_attr == [1, 1337, 1, 123]

    pydase_client.proxy.list_attr.clear()
    assert pydase_client.proxy.list_attr == []


def test_dict(pydase_client: pydase.Client) -> None:
    pydase_client.proxy.dict_attr["foo"].name = "foo"
    assert pydase_client.proxy.dict_attr["foo"].name == "foo"
    assert pydase_client.proxy.dict_attr["dotted.key"].name == "foo"

    # pop will not return anything as the server object was deleted
    assert pydase_client.proxy.dict_attr.pop("dotted.key") is None

    # pop will remove the dictionary entry on the server
    assert list(pydase_client.proxy.dict_attr.keys()) == ["foo"]

    pydase_client.proxy.dict_attr["non_existent_key"] = "Hello"
    assert pydase_client.proxy.dict_attr["non_existent_key"] == "Hello"


def test_tab_completion(pydase_client: pydase.Client) -> None:
    # Tab completion gets its suggestions from the __dir__ class method
    assert all(
        x in pydase_client.proxy.__dir__()
        for x in [
            "dict_attr",
            "list_attr",
            "my_method",
            "my_property",
            "name",
            "sub_service",
        ]
    )


def test_context_manager(pydase_client: pydase.Client) -> None:
    client = pydase.Client(url="ws://localhost:9999")

    assert client.proxy.connected

    with client:
        client.proxy.my_property = 1337.01
        assert client.proxy.my_property == 1337.01

    assert not client.proxy.connected


def test_client_id(
    pydase_client: pydase.Client, caplog: pytest.LogCaptureFixture
) -> None:
    import socket

    pydase.Client(url="ws://localhost:9999")

    assert f"Client [id={socket.gethostname()}]" in caplog.text
    caplog.clear()

    pydase.Client(url="ws://localhost:9999", client_id="my_service")
    assert "Client [id=my_service] connected" in caplog.text


def test_get_value(
    pydase_client: pydase.Client, caplog: pytest.LogCaptureFixture
) -> None:
    pydase_client.update_value("sub_service.name", "Other name")

    assert pydase_client.get_value("sub_service.name") == "Other name"

    assert (
        pydase_client.trigger_method("my_async_method", input_str="Hello World")
        == "Hello World"
    )
