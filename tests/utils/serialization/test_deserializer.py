import enum
from typing import Any

import pydase.components
import pydase.units as u
import pytest
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.serializer import dump
from pydase.utils.serialization.types import SerializedObject


class MyEnum(enum.Enum):
    FINISHED = "finished"
    RUNNING = "running"


class MyService(pydase.DataService):
    name = "MyService"


@pytest.mark.parametrize(
    "obj, obj_serialization",
    [
        (
            1,
            {
                "full_access_path": "",
                "type": "int",
                "value": 1,
                "readonly": False,
                "doc": None,
            },
        ),
        (
            1.0,
            {
                "full_access_path": "",
                "type": "float",
                "value": 1.0,
                "readonly": False,
                "doc": None,
            },
        ),
        (
            True,
            {
                "full_access_path": "",
                "type": "bool",
                "value": True,
                "readonly": False,
                "doc": None,
            },
        ),
        (
            u.Quantity(10, "m"),
            {
                "full_access_path": "",
                "type": "Quantity",
                "value": {"magnitude": 10, "unit": "meter"},
                "readonly": False,
                "doc": None,
            },
        ),
        (
            [1.0],
            {
                "full_access_path": "",
                "value": [
                    {
                        "full_access_path": "[0]",
                        "doc": None,
                        "readonly": False,
                        "type": "float",
                        "value": 1.0,
                    }
                ],
                "type": "list",
                "doc": None,
                "readonly": False,
            },
        ),
        (
            {"key": 1.0},
            {
                "full_access_path": "",
                "value": {
                    "key": {
                        "full_access_path": '["key"]',
                        "doc": None,
                        "readonly": False,
                        "type": "float",
                        "value": 1.0,
                    }
                },
                "type": "dict",
                "doc": None,
                "readonly": False,
            },
        ),
    ],
)
def test_loads_primitive_types(obj: Any, obj_serialization: SerializedObject) -> None:
    assert loads(obj_serialization) == obj


@pytest.mark.parametrize(
    "obj, obj_serialization",
    [
        (
            MyEnum.RUNNING,
            {
                "full_access_path": "",
                "value": "RUNNING",
                "type": "Enum",
                "doc": "MyEnum description",
                "readonly": False,
                "name": "MyEnum",
                "enum": {"RUNNING": "running", "FINISHED": "finished"},
            },
        ),
        (
            MyService(),
            {
                "full_access_path": "",
                "value": {
                    "name": {
                        "full_access_path": "name",
                        "doc": None,
                        "readonly": False,
                        "type": "str",
                        "value": "MyService",
                    }
                },
                "type": "DataService",
                "doc": None,
                "readonly": False,
                "name": "MyService",
            },
        ),
    ],
)
def test_loads_advanced_types(obj: Any, obj_serialization: SerializedObject) -> None:
    assert dump(loads(obj_serialization)) == dump(obj)
