import asyncio
from enum import Enum

import pytest

import pydase
import pydase.units as u
from pydase.components.coloured_enum import ColouredEnum
from pydase.utils.serialization import dump


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (1, {"type": "int", "value": 1, "readonly": False, "doc": None}),
        (1.0, {"type": "float", "value": 1.0, "readonly": False, "doc": None}),
        (True, {"type": "bool", "value": True, "readonly": False, "doc": None}),
        (
            u.Quantity(10, "m"),
            {
                "type": "Quantity",
                "value": {"magnitude": 10, "unit": "meter"},
                "readonly": False,
                "doc": None,
            },
        ),
    ],
)
def test_dump(test_input, expected):
    assert dump(test_input) == expected


def test_enum_serialize() -> None:
    class EnumClass(Enum):
        FOO = "foo"
        BAR = "bar"

    class EnumAttribute(pydase.DataService):
        def __init__(self) -> None:
            self.some_enum = EnumClass.FOO
            super().__init__()

    class EnumPropertyWithoutSetter(pydase.DataService):
        def __init__(self) -> None:
            self._some_enum = EnumClass.FOO
            super().__init__()

        @property
        def some_enum(self) -> EnumClass:
            return self._some_enum

    class EnumPropertyWithSetter(pydase.DataService):
        def __init__(self) -> None:
            self._some_enum = EnumClass.FOO
            super().__init__()

        @property
        def some_enum(self) -> EnumClass:
            return self._some_enum

        @some_enum.setter
        def some_enum(self, value: EnumClass) -> None:
            self._some_enum = value

    assert dump(EnumAttribute())["value"] == {
        "some_enum": {
            "type": "Enum",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": False,
            "doc": None,
        }
    }
    assert dump(EnumPropertyWithoutSetter())["value"] == {
        "some_enum": {
            "type": "Enum",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": True,
            "doc": None,
        }
    }
    assert dump(EnumPropertyWithSetter())["value"] == {
        "some_enum": {
            "type": "Enum",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": False,
            "doc": None,
        }
    }


def test_ColouredEnum_serialize() -> None:
    class Status(ColouredEnum):
        PENDING = "#FFA500"
        RUNNING = "#0000FF80"
        PAUSED = "rgb(169, 169, 169)"
        RETRYING = "rgba(255, 255, 0, 0.3)"
        COMPLETED = "hsl(120, 100%, 50%)"
        FAILED = "hsla(0, 100%, 50%, 0.7)"
        CANCELLED = "SlateGray"

    assert dump(Status.FAILED) == {
        "type": "ColouredEnum",
        "value": "FAILED",
        "enum": {
            "CANCELLED": "SlateGray",
            "COMPLETED": "hsl(120, 100%, 50%)",
            "FAILED": "hsla(0, 100%, 50%, 0.7)",
            "PAUSED": "rgb(169, 169, 169)",
            "PENDING": "#FFA500",
            "RETRYING": "rgba(255, 255, 0, 0.3)",
            "RUNNING": "#0000FF80",
        },
        "readonly": False,
        "doc": None,
    }


def test_method_serialization() -> None:
    class ClassWithMethod(pydase.DataService):
        def some_method(self) -> str:
            return "some method"

        async def some_task(self, sleep_time: int) -> None:
            while True:
                await asyncio.sleep(sleep_time)

    instance = ClassWithMethod()
    instance.start_some_task(10)  # type: ignore

    assert dump(instance)["value"] == {
        "some_method": {
            "async": False,
            "doc": None,
            "parameters": {},
            "readonly": True,
            "type": "method",
            "value": None,
        },
        "some_task": {
            "async": True,
            "doc": None,
            "parameters": {"sleep_time": "int"},
            "readonly": True,
            "type": "method",
            "value": {"sleep_time": 10},
        },
    }


def test_methods_with_type_hints() -> None:
    def method_without_type_hint(arg_without_type_hint) -> None:
        pass

    def method_with_type_hint(some_argument: int) -> None:
        pass

    def method_with_union_type_hint(some_argument: int | float) -> None:
        pass

    assert dump(method_without_type_hint) == {
        "async": False,
        "doc": None,
        "parameters": {"arg_without_type_hint": None},
        "readonly": True,
        "type": "method",
        "value": None,
    }

    assert dump(method_with_type_hint) == {
        "async": False,
        "doc": None,
        "parameters": {"some_argument": "int"},
        "readonly": True,
        "type": "method",
        "value": None,
    }

    assert dump(method_with_union_type_hint) == {
        "async": False,
        "doc": None,
        "parameters": {"some_argument": "int | float"},
        "readonly": True,
        "type": "method",
        "value": None,
    }


def test_list_serialization() -> None:
    class MySubclass(pydase.DataService):
        _name = "hi"
        bool_attr = True
        int_attr = 1

        @property
        def name(self) -> str:
            return self._name

    class ClassWithListAttribute(pydase.DataService):
        list_attr = [1, MySubclass()]

    instance = ClassWithListAttribute()

    assert dump(instance)["value"] == {
        "list_attr": {
            "doc": None,
            "readonly": False,
            "type": "list",
            "value": [
                {"doc": None, "readonly": False, "type": "int", "value": 1},
                {
                    "doc": None,
                    "readonly": False,
                    "type": "DataService",
                    "value": {
                        "bool_attr": {
                            "doc": None,
                            "readonly": False,
                            "type": "bool",
                            "value": True,
                        },
                        "int_attr": {
                            "doc": None,
                            "readonly": False,
                            "type": "int",
                            "value": 1,
                        },
                        "name": {
                            "doc": None,
                            "readonly": True,
                            "type": "str",
                            "value": "hi",
                        },
                    },
                },
            ],
        }
    }


def test_dict_serialization() -> None:
    class MyClass(pydase.DataService):
        name = "my class"

    test_dict = {
        "int_key": 1,
        "float_key": 1.0,
        "bool_key": True,
        "Quantity_key": 1.0 * u.units.s,
        "DataService_key": MyClass(),
    }

    assert dump(test_dict) == {
        "doc": None,
        "readonly": False,
        "type": "dict",
        "value": {
            "DataService_key": {
                "doc": None,
                "readonly": False,
                "type": "DataService",
                "value": {
                    "name": {
                        "doc": None,
                        "readonly": False,
                        "type": "str",
                        "value": "my class",
                    }
                },
            },
            "Quantity_key": {
                "doc": None,
                "readonly": False,
                "type": "Quantity",
                "value": {"magnitude": 1.0, "unit": "s"},
            },
            "bool_key": {"doc": None, "readonly": False, "type": "bool", "value": True},
            "float_key": {
                "doc": None,
                "readonly": False,
                "type": "float",
                "value": 1.0,
            },
            "int_key": {"doc": None, "readonly": False, "type": "int", "value": 1},
        },
    }
