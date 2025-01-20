import threading
from collections.abc import Generator
from typing import Any

import pydase
import pytest
import socketio
from pydase.utils.serialization.deserializer import Deserializer


@pytest.fixture()
def pydase_server() -> Generator[None, None, None]:
    class SubService(pydase.DataService):
        name = "SubService"

    subservice_instance = SubService()

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._readonly_attr = "MyService"
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
        def readonly_attr(self) -> str:
            return self._readonly_attr

        def my_method(self, input_str: str) -> str:
            return f"{input_str}: my_method"

        async def my_async_method(self, input_str: str) -> str:
            return f"{input_str}: my_async_method"

    server = pydase.Server(MyService(), web_port=9997)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    yield


@pytest.mark.parametrize(
    "access_path, expected",
    [
        (
            "readonly_attr",
            {
                "full_access_path": "readonly_attr",
                "doc": None,
                "readonly": False,
                "type": "str",
                "value": "MyService",
            },
        ),
        (
            "sub_service.name",
            {
                "full_access_path": "sub_service.name",
                "doc": None,
                "readonly": False,
                "type": "str",
                "value": "SubService",
            },
        ),
        (
            "list_attr[0]",
            {
                "full_access_path": "list_attr[0]",
                "doc": None,
                "readonly": False,
                "type": "int",
                "value": 1,
            },
        ),
        (
            'dict_attr["foo"]',
            {
                "full_access_path": 'dict_attr["foo"]',
                "doc": None,
                "name": "SubService",
                "readonly": False,
                "type": "DataService",
                "value": {
                    "name": {
                        "doc": None,
                        "full_access_path": 'dict_attr["foo"].name',
                        "readonly": False,
                        "type": "str",
                        "value": "SubService",
                    }
                },
            },
        ),
    ],
)
@pytest.mark.asyncio()
async def test_get_value(
    access_path: str,
    expected: dict[str, Any],
    pydase_server: None,
) -> None:
    client = socketio.AsyncClient()
    await client.connect(
        "http://localhost:9997", socketio_path="/ws/socket.io", transports=["websocket"]
    )
    response = await client.call("get_value", access_path)
    assert response == expected
    await client.disconnect()


@pytest.mark.parametrize(
    "access_path, new_value, ok",
    [
        (
            "sub_service.name",
            {
                "full_access_path": "sub_service.name",
                "doc": None,
                "readonly": False,
                "type": "str",
                "value": "New Name",
            },
            True,
        ),
        (
            "list_attr[0]",
            {
                "full_access_path": "list_attr[0]",
                "doc": None,
                "readonly": False,
                "type": "int",
                "value": 11,
            },
            True,
        ),
        (
            'dict_attr["foo"].name',
            {
                "full_access_path": 'dict_attr["foo"].name',
                "doc": None,
                "readonly": False,
                "type": "str",
                "value": "foo name",
            },
            True,
        ),
        (
            "readonly_attr",
            {
                "full_access_path": "readonly_attr",
                "doc": None,
                "readonly": True,
                "type": "str",
                "value": "Other Name",
            },
            False,
        ),
        (
            "invalid_attribute",
            {
                "full_access_path": "invalid_attribute",
                "doc": None,
                "readonly": False,
                "type": "float",
                "value": 12.0,
            },
            False,
        ),
    ],
)
@pytest.mark.asyncio()
async def test_update_value(
    access_path: str,
    new_value: dict[str, Any],
    ok: bool,
    pydase_server: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = socketio.AsyncClient()
    await client.connect(
        "http://localhost:9997", socketio_path="/ws/socket.io", transports=["websocket"]
    )
    response = await client.call(
        "update_value",
        {"access_path": access_path, "value": new_value},
    )

    if ok:
        assert response is None
    else:
        assert response["type"] == "Exception"

    await client.disconnect()


@pytest.mark.parametrize(
    "access_path, expected, ok",
    [
        (
            "my_method",
            "Hello from function: my_method",
            True,
        ),
        (
            "my_async_method",
            "Hello from function: my_async_method",
            True,
        ),
        (
            "invalid_method",
            None,
            False,
        ),
    ],
)
@pytest.mark.asyncio()
async def test_trigger_method(
    access_path: str,
    expected: Any,
    ok: bool,
    pydase_server: pydase.DataService,
) -> None:
    client = socketio.AsyncClient()
    await client.connect(
        "http://localhost:9997", socketio_path="/ws/socket.io", transports=["websocket"]
    )
    response = await client.call(
        "trigger_method",
        {
            "access_path": access_path,
            "kwargs": {
                "full_access_path": "",
                "type": "dict",
                "value": {
                    "input_str": {
                        "docs": None,
                        "full_access_path": "",
                        "readonly": False,
                        "type": "str",
                        "value": "Hello from function",
                    },
                },
            },
        },
    )

    if ok:
        content = Deserializer.deserialize(response)
        assert content == expected
    else:
        assert response["type"] == "Exception"

    await client.disconnect()


@pytest.mark.parametrize(
    "headers, log_id",
    [
        ({}, "sid="),
        (
            {
                "X-Client-Id": "client-header",
            },
            "id=client-header",
        ),
        (
            {
                "Remote-User": "Remote User",
            },
            "user=Remote User",
        ),
        (
            {
                "X-Client-Id": "client-header",
                "Remote-User": "Remote User",
            },
            "user=Remote User",
        ),
    ],
)
@pytest.mark.asyncio()
async def test_client_information_logging(
    headers: dict[str, str],
    log_id: str,
    pydase_server: pydase.DataService,
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = socketio.AsyncClient()
    await client.connect(
        "http://localhost:9997",
        socketio_path="/ws/socket.io",
        transports=["websocket"],
        headers=headers,
    )
    await client.call("get_value", "readonly_attr")

    assert log_id in caplog.text

    await client.disconnect()
