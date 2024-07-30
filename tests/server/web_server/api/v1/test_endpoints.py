import json
import threading
from collections.abc import Generator
from typing import Any

import aiohttp
import pydase
import pytest


@pytest.fixture(scope="module")
def pydase_server() -> Generator[None, None, None]:
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

    server = pydase.Server(MyService(), web_port=9998)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    yield


@pytest.mark.parametrize(
    "access_path, expected",
    [
        (
            "name",
            {
                "full_access_path": "name",
                "doc": None,
                "readonly": True,
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
@pytest.mark.asyncio(scope="module")
async def test_get_value(
    access_path: str,
    expected: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
    pydase_server: None,
) -> None:
    async with aiohttp.ClientSession("http://localhost:9998") as session:
        resp = await session.get(f"/api/v1/get_value?access_path={access_path}")
        content = json.loads(await resp.text())
        assert content == expected


@pytest.mark.parametrize(
    "access_path, new_value",
    [
        (
            "name",
            {
                "full_access_path": "name",
                "doc": None,
                "readonly": True,
                "type": "str",
                "value": "Other Name",
            },
        ),
        (
            "sub_service.name",
            {
                "full_access_path": "sub_service.name",
                "doc": None,
                "readonly": False,
                "type": "str",
                "value": "New Name",
            },
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
        ),
        (
            "my_property",
            {
                "full_access_path": "my_property",
                "doc": None,
                "readonly": False,
                "type": "float",
                "value": 12.0,
            },
        ),
    ],
)
@pytest.mark.asyncio(scope="module")
async def test_update_value(
    access_path: str,
    new_value: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
    pydase_server: None,
) -> None:
    async with aiohttp.ClientSession("http://localhost:9998") as session:
        resp = await session.put(
            "/api/v1/update_value",
            json={"access_path": access_path, "value": new_value},
        )
        assert resp.ok
