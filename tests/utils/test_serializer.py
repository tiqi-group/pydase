import asyncio
from enum import Enum
from typing import Any

import pydase
import pydase.units as u
import pytest
from pydase.components.coloured_enum import ColouredEnum
from pydase.utils.serializer import (
    SerializationPathError,
    dump,
    get_nested_dict_by_path,
    get_next_level_dict_by_key,
    serialized_dict_is_nested_object,
    set_nested_value_by_path,
)


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
def test_dump(test_input: Any, expected: dict[str, Any]) -> None:
    assert dump(test_input) == expected


def test_enum_serialize() -> None:
    class EnumClass(Enum):
        FOO = "foo"
        BAR = "bar"

    class EnumAttribute(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.some_enum = EnumClass.FOO

    class EnumPropertyWithoutSetter(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._some_enum = EnumClass.FOO

        @property
        def some_enum(self) -> EnumClass:
            return self._some_enum

    class EnumPropertyWithSetter(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self._some_enum = EnumClass.FOO

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


@pytest.mark.asyncio
async def test_method_serialization() -> None:
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


def test_derived_data_service_serialization() -> None:
    class BaseService(pydase.DataService):
        class_attr = 1337

        def __init__(self) -> None:
            super().__init__()
            self._name = "Service"

        @property
        def name(self) -> str:
            return self._name

        @name.setter
        def name(self, value: str) -> None:
            self._name = value

    class DerivedService(BaseService):
        ...

    base_instance = BaseService()
    service_instance = DerivedService()
    assert service_instance.serialize() == base_instance.serialize()


@pytest.fixture
def setup_dict():
    class MySubclass(pydase.DataService):
        attr3 = 1.0
        list_attr = [1.0, 1]

    class ServiceClass(pydase.DataService):
        attr1 = 1.0
        attr2 = MySubclass()
        attr_list = [0, 1, MySubclass()]

    return ServiceClass().serialize()


def test_update_attribute(setup_dict):
    set_nested_value_by_path(setup_dict, "attr1", 15)
    assert setup_dict["attr1"]["value"] == 15


def test_update_nested_attribute(setup_dict):
    set_nested_value_by_path(setup_dict, "attr2.attr3", 25.0)
    assert setup_dict["attr2"]["value"]["attr3"]["value"] == 25.0


def test_update_list_entry(setup_dict):
    set_nested_value_by_path(setup_dict, "attr_list[1]", 20)
    assert setup_dict["attr_list"]["value"][1]["value"] == 20


def test_update_list_append(setup_dict):
    set_nested_value_by_path(setup_dict, "attr_list[3]", 20)
    assert setup_dict["attr_list"]["value"][3]["value"] == 20


def test_update_invalid_list_index(setup_dict, caplog: pytest.LogCaptureFixture):
    set_nested_value_by_path(setup_dict, "attr_list[10]", 30)
    assert (
        "Error occured trying to change 'attr_list[10]': list index "
        "out of range" in caplog.text
    )


def test_update_invalid_path(
    setup_dict: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    set_nested_value_by_path(setup_dict, "invalid_path", 30)
    assert (
        "Error occured trying to access the key 'invalid_path': it is either "
        "not present in the current dictionary or its value does not contain "
        "a 'value' key." in caplog.text
    )


def test_update_list_inside_class(setup_dict: dict[str, Any]) -> None:
    set_nested_value_by_path(setup_dict, "attr2.list_attr[1]", 40)
    assert setup_dict["attr2"]["value"]["list_attr"]["value"][1]["value"] == 40


def test_update_class_attribute_inside_list(setup_dict: dict[str, Any]) -> None:
    set_nested_value_by_path(setup_dict, "attr_list[2].attr3", 50)
    assert setup_dict["attr_list"]["value"][2]["value"]["attr3"]["value"] == 50


def test_get_next_level_attribute_nested_dict(setup_dict: dict[str, Any]) -> None:
    nested_dict = get_next_level_dict_by_key(setup_dict, "attr1")
    assert nested_dict == setup_dict["attr1"]


def test_get_next_level_list_entry_nested_dict(setup_dict: dict[str, Any]) -> None:
    nested_dict = get_next_level_dict_by_key(setup_dict, "attr_list[0]")
    assert nested_dict == setup_dict["attr_list"]["value"][0]


def test_get_next_level_invalid_path_nested_dict(setup_dict: dict[str, Any]) -> None:
    with pytest.raises(SerializationPathError):
        get_next_level_dict_by_key(setup_dict, "invalid_path")


def test_get_next_level_invalid_list_index(setup_dict: dict[str, Any]) -> None:
    with pytest.raises(SerializationPathError):
        get_next_level_dict_by_key(setup_dict, "attr_list[10]")


def test_get_attribute(setup_dict: dict[str, Any]) -> None:
    nested_dict = get_nested_dict_by_path(setup_dict, "attr1")
    assert nested_dict["value"] == 1.0


def test_get_nested_attribute(setup_dict: dict[str, Any]) -> None:
    nested_dict = get_nested_dict_by_path(setup_dict, "attr2.attr3")
    assert nested_dict["value"] == 1.0


def test_get_list_entry(setup_dict: dict[str, Any]) -> None:
    nested_dict = get_nested_dict_by_path(setup_dict, "attr_list[1]")
    assert nested_dict["value"] == 1


def test_get_list_inside_class(setup_dict: dict[str, Any]) -> None:
    nested_dict = get_nested_dict_by_path(setup_dict, "attr2.list_attr[1]")
    assert nested_dict["value"] == 1.0


def test_get_class_attribute_inside_list(setup_dict: dict[str, Any]) -> None:
    nested_dict = get_nested_dict_by_path(setup_dict, "attr_list[2].attr3")
    assert nested_dict["value"] == 1.0


def test_get_invalid_list_index(setup_dict: dict[str, Any]) -> None:
    with pytest.raises(SerializationPathError):
        get_nested_dict_by_path(setup_dict, "attr_list[10]")


def test_get_invalid_path(setup_dict: dict[str, Any]) -> None:
    with pytest.raises(SerializationPathError):
        get_nested_dict_by_path(setup_dict, "invalid_path")


def test_serialized_dict_is_nested_object() -> None:
    serialized_dict = {
        "list_attr": {
            "type": "list",
            "value": [
                {"type": "float", "value": 1.4, "readonly": False, "doc": None},
                {"type": "float", "value": 2.0, "readonly": False, "doc": None},
            ],
            "readonly": False,
            "doc": None,
        },
        "my_slider": {
            "type": "NumberSlider",
            "value": {
                "max": {
                    "type": "float",
                    "value": 101.0,
                    "readonly": False,
                    "doc": "The min property.",
                },
                "min": {
                    "type": "float",
                    "value": 1.0,
                    "readonly": False,
                    "doc": "The min property.",
                },
                "step_size": {
                    "type": "float",
                    "value": 2.0,
                    "readonly": False,
                    "doc": "The min property.",
                },
                "value": {
                    "type": "float",
                    "value": 1.0,
                    "readonly": False,
                    "doc": "The value property.",
                },
            },
            "readonly": False,
            "doc": None,
        },
        "string": {
            "type": "str",
            "value": "Another name",
            "readonly": True,
            "doc": None,
        },
        "float": {
            "type": "int",
            "value": 10,
            "readonly": False,
            "doc": None,
        },
        "unit": {
            "type": "Quantity",
            "value": {"magnitude": 12.0, "unit": "A"},
            "readonly": False,
            "doc": None,
        },
        "state": {
            "type": "ColouredEnum",
            "value": "FAILED",
            "readonly": True,
            "doc": None,
            "enum": {
                "RUNNING": "#0000FF80",
                "COMPLETED": "hsl(120, 100%, 50%)",
                "FAILED": "hsla(0, 100%, 50%, 0.7)",
            },
        },
        "subservice": {
            "type": "DataService",
            "value": {
                "name": {
                    "type": "str",
                    "value": "SubService",
                    "readonly": False,
                    "doc": None,
                }
            },
            "readonly": False,
            "doc": None,
        },
    }

    assert serialized_dict_is_nested_object(serialized_dict["list_attr"])
    assert serialized_dict_is_nested_object(serialized_dict["my_slider"])
    assert serialized_dict_is_nested_object(serialized_dict["subservice"])

    assert not serialized_dict_is_nested_object(
        serialized_dict["list_attr"]["value"][0]  # type: ignore[index]
    )
    assert not serialized_dict_is_nested_object(serialized_dict["string"])
    assert not serialized_dict_is_nested_object(serialized_dict["unit"])
    assert not serialized_dict_is_nested_object(serialized_dict["float"])
    assert not serialized_dict_is_nested_object(serialized_dict["state"])
