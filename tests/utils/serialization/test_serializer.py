import enum
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

import pydase
import pydase.units as u
import pytest
from pydase.components.coloured_enum import ColouredEnum
from pydase.task.task_status import TaskStatus
from pydase.utils.decorators import frontend
from pydase.utils.serialization.serializer import (
    SerializationPathError,
    SerializedObject,
    add_prefix_to_full_access_path,
    dump,
    generate_serialized_data_paths,
    get_container_item_by_key,
    get_data_paths_from_serialized_object,
    get_nested_dict_by_path,
    serialized_dict_is_nested_object,
    set_nested_value_by_path,
)


class MyEnum(enum.Enum):
    """MyEnum description"""

    RUNNING = "running"
    FINISHED = "finished"


class MySubclass(pydase.DataService):
    attr3 = 1.0
    list_attr: ClassVar[list[Any]] = [1.0, 1]
    some_quantity: u.Quantity = 1.0 * u.units.A


class ServiceClass(pydase.DataService):
    attr1 = 1.0
    attr2 = MySubclass()
    enum_attr = MyEnum.RUNNING
    attr_list: ClassVar[list[Any]] = [0, 1, MySubclass()]
    dict_attr: ClassVar[dict[Any, Any]] = {"foo": 1.0, "bar": {"foo": "bar"}}

    def my_task(self) -> None:
        pass


service_instance = ServiceClass()


@pytest.mark.parametrize(
    "test_input, expected",
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
            datetime.fromisoformat("2024-07-09 15:37:08.249845"),
            {
                "full_access_path": "",
                "type": "datetime",
                "value": "2024-07-09 15:37:08.249845",
                "readonly": True,
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
            "full_access_path": "some_enum",
            "type": "Enum",
            "name": "EnumClass",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": False,
            "doc": None,
        }
    }
    assert dump(EnumPropertyWithoutSetter())["value"] == {
        "some_enum": {
            "full_access_path": "some_enum",
            "type": "Enum",
            "name": "EnumClass",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": True,
            "doc": None,
        }
    }
    assert dump(EnumPropertyWithSetter())["value"] == {
        "some_enum": {
            "full_access_path": "some_enum",
            "type": "Enum",
            "name": "EnumClass",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": False,
            "doc": None,
        }
    }


def test_ColouredEnum_serialize() -> None:
    class Status(ColouredEnum):
        """Status description."""

        PENDING = "#FFA500"
        RUNNING = "#0000FF80"
        PAUSED = "rgb(169, 169, 169)"
        RETRYING = "rgba(255, 255, 0, 0.3)"
        COMPLETED = "hsl(120, 100%, 50%)"
        FAILED = "hsla(0, 100%, 50%, 0.7)"
        CANCELLED = "SlateGray"

    assert dump(Status.FAILED) == {
        "full_access_path": "",
        "type": "ColouredEnum",
        "name": "Status",
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
        "doc": "Status description.",
    }


@pytest.mark.asyncio(scope="module")
async def test_method_serialization() -> None:
    class ClassWithMethod(pydase.DataService):
        def some_method(self) -> str:
            return "some method"

        async def some_task(self) -> None:
            pass

    instance = ClassWithMethod()

    assert dump(instance)["value"] == {
        "some_method": {
            "full_access_path": "some_method",
            "type": "method",
            "value": None,
            "readonly": True,
            "doc": None,
            "async": False,
            "signature": {"parameters": {}, "return_annotation": {}},
            "frontend_render": False,
        },
        "some_task": {
            "full_access_path": "some_task",
            "type": "method",
            "value": None,
            "readonly": True,
            "doc": None,
            "async": True,
            "signature": {
                "parameters": {},
                "return_annotation": {},
            },
            "frontend_render": True,
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
        "full_access_path": "",
        "async": False,
        "doc": None,
        "signature": {
            "parameters": {
                "arg_without_type_hint": {
                    "annotation": "<class 'inspect._empty'>",
                    "default": {},
                }
            },
            "return_annotation": {},
        },
        "readonly": True,
        "type": "method",
        "value": None,
        "frontend_render": False,
    }

    assert dump(method_with_type_hint) == {
        "full_access_path": "",
        "type": "method",
        "value": None,
        "readonly": True,
        "doc": None,
        "async": False,
        "signature": {
            "parameters": {
                "some_argument": {"annotation": "<class 'int'>", "default": {}}
            },
            "return_annotation": {},
        },
        "frontend_render": False,
    }
    assert dump(method_with_union_type_hint) == {
        "full_access_path": "",
        "type": "method",
        "value": None,
        "readonly": True,
        "doc": None,
        "async": False,
        "signature": {
            "parameters": {
                "some_argument": {"annotation": "int | float", "default": {}}
            },
            "return_annotation": {},
        },
        "frontend_render": False,
    }


def test_exposed_function_serialization() -> None:
    class MyService(pydase.DataService):
        @frontend
        def some_method(self) -> None:
            pass

    @frontend
    def some_function() -> None:
        pass

    assert dump(MyService().some_method) == {
        "full_access_path": "",
        "type": "method",
        "value": None,
        "readonly": True,
        "doc": None,
        "async": False,
        "signature": {"parameters": {}, "return_annotation": {}},
        "frontend_render": True,
    }

    assert dump(some_function) == {
        "full_access_path": "",
        "type": "method",
        "value": None,
        "readonly": True,
        "doc": None,
        "async": False,
        "signature": {"parameters": {}, "return_annotation": {}},
        "frontend_render": True,
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
            "full_access_path": "list_attr",
            "doc": None,
            "readonly": False,
            "type": "list",
            "value": [
                {
                    "full_access_path": "list_attr[0]",
                    "doc": None,
                    "readonly": False,
                    "type": "int",
                    "value": 1,
                },
                {
                    "full_access_path": "list_attr[1]",
                    "doc": None,
                    "readonly": False,
                    "type": "DataService",
                    "name": "MySubclass",
                    "value": {
                        "bool_attr": {
                            "full_access_path": "list_attr[1].bool_attr",
                            "doc": None,
                            "readonly": False,
                            "type": "bool",
                            "value": True,
                        },
                        "int_attr": {
                            "full_access_path": "list_attr[1].int_attr",
                            "doc": None,
                            "readonly": False,
                            "type": "int",
                            "value": 1,
                        },
                        "name": {
                            "full_access_path": "list_attr[1].name",
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
        "1.0": 1.0,
        "bool_key": True,
        "Quantity_key": 1.0 * u.units.s,
        "DataService_key": MyClass(),
    }

    assert dump(test_dict) == {
        "full_access_path": "",
        "doc": None,
        "readonly": False,
        "type": "dict",
        "value": {
            "DataService_key": {
                "full_access_path": '["DataService_key"]',
                "name": "MyClass",
                "doc": None,
                "readonly": False,
                "type": "DataService",
                "value": {
                    "name": {
                        "full_access_path": '["DataService_key"].name',
                        "doc": None,
                        "readonly": False,
                        "type": "str",
                        "value": "my class",
                    }
                },
            },
            "Quantity_key": {
                "full_access_path": '["Quantity_key"]',
                "doc": None,
                "readonly": False,
                "type": "Quantity",
                "value": {"magnitude": 1.0, "unit": "s"},
            },
            "bool_key": {
                "full_access_path": '["bool_key"]',
                "doc": None,
                "readonly": False,
                "type": "bool",
                "value": True,
            },
            "1.0": {
                "full_access_path": '["1.0"]',
                "doc": None,
                "readonly": False,
                "type": "float",
                "value": 1.0,
            },
            "int_key": {
                "full_access_path": '["int_key"]',
                "doc": None,
                "readonly": False,
                "type": "int",
                "value": 1,
            },
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

    class DerivedService(BaseService): ...

    base_service_serialization = dump(BaseService())
    derived_service_serialization = dump(DerivedService())

    # Names of the classes obviously differ
    base_service_serialization.pop("name")
    derived_service_serialization.pop("name")

    assert base_service_serialization == derived_service_serialization


@pytest.fixture
def setup_dict() -> dict[str, Any]:
    return ServiceClass().serialize()["value"]  # type: ignore


@pytest.mark.parametrize(
    "serialized_object, attr_name, allow_append, expected",
    [
        (
            dump(service_instance)["value"],
            "attr1",
            False,
            {
                "doc": None,
                "full_access_path": "attr1",
                "readonly": False,
                "type": "float",
                "value": 1.0,
            },
        ),
        (
            dump(service_instance.attr_list)["value"],
            "[0]",
            False,
            {
                "doc": None,
                "full_access_path": "[0]",
                "readonly": False,
                "type": "int",
                "value": 0,
            },
        ),
        (
            dump(service_instance.attr_list)["value"],
            "[3]",
            True,
            {
                # we do not know the full_access_path of this entry within the
                # serialized object
                "full_access_path": "",
                "value": None,
                "type": "None",
                "doc": None,
                "readonly": False,
            },
        ),
        (
            dump(service_instance.attr_list)["value"],
            "[3]",
            False,
            SerializationPathError,
        ),
        (
            dump(service_instance.dict_attr)["value"],
            "['foo']",
            False,
            {
                "full_access_path": '["foo"]',
                "value": 1.0,
                "type": "float",
                "doc": None,
                "readonly": False,
            },
        ),
        (
            dump(service_instance.dict_attr)["value"],
            "['unset_key']",
            True,
            {
                # we do not know the full_access_path of this entry within the
                # serialized object
                "full_access_path": "",
                "value": None,
                "type": "None",
                "doc": None,
                "readonly": False,
            },
        ),
        (
            dump(service_instance.dict_attr)["value"],
            "['unset_key']",
            False,
            SerializationPathError,
        ),
        (
            dump(service_instance)["value"],
            "invalid_path",
            True,
            {
                # we do not know the full_access_path of this entry within the
                # serialized object
                "full_access_path": "",
                "value": None,
                "type": "None",
                "doc": None,
                "readonly": False,
            },
        ),
        (
            dump(service_instance)["value"],
            "invalid_path",
            False,
            SerializationPathError,
        ),
    ],
)
def test_get_container_item_by_key(
    serialized_object: dict[str, Any], attr_name: str, allow_append: bool, expected: Any
) -> None:
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            get_container_item_by_key(
                serialized_object, attr_name, allow_append=allow_append
            )
    else:
        nested_dict = get_container_item_by_key(
            serialized_object, attr_name, allow_append=allow_append
        )
        assert nested_dict == expected


def test_update_attribute(setup_dict: dict[str, Any]) -> None:
    set_nested_value_by_path(setup_dict, "attr1", 15)
    assert setup_dict["attr1"]["value"] == 15


def test_update_nested_attribute(setup_dict: dict[str, Any]) -> None:
    set_nested_value_by_path(setup_dict, "attr2.attr3", 25.0)
    assert setup_dict["attr2"]["value"]["attr3"]["value"] == 25.0


def test_update_float_attribute_to_enum(setup_dict: dict[str, Any]) -> None:
    set_nested_value_by_path(setup_dict, "attr2.attr3", MyEnum.RUNNING)
    assert setup_dict["attr2"]["value"]["attr3"] == {
        "full_access_path": "attr2.attr3",
        "name": "MyEnum",
        "doc": "MyEnum description",
        "enum": {"FINISHED": "finished", "RUNNING": "running"},
        "readonly": False,
        "type": "Enum",
        "value": "RUNNING",
    }


def test_update_enum_attribute_to_float(setup_dict: dict[str, Any]) -> None:
    set_nested_value_by_path(setup_dict, "enum_attr", 1.01)
    assert setup_dict["enum_attr"] == {
        "full_access_path": "enum_attr",
        "doc": None,
        "readonly": False,
        "type": "float",
        "value": 1.01,
    }


def test_update_task_state(setup_dict: dict[str, Any]) -> None:
    assert setup_dict["my_task"] == {
        "full_access_path": "my_task",
        "async": False,
        "doc": None,
        "frontend_render": False,
        "readonly": True,
        "signature": {"parameters": {}, "return_annotation": {}},
        "type": "method",
        "value": None,
    }
    set_nested_value_by_path(setup_dict, "my_task", TaskStatus.RUNNING)
    assert setup_dict["my_task"] == {
        "full_access_path": "my_task",
        "async": False,
        "doc": None,
        "frontend_render": False,
        "readonly": True,
        "signature": {"parameters": {}, "return_annotation": {}},
        "type": "method",
        "value": "RUNNING",
    }


def test_update_list_entry(setup_dict: dict[str, SerializedObject]) -> None:
    set_nested_value_by_path(setup_dict, "attr_list[1]", 20)
    assert setup_dict["attr_list"]["value"][1]["value"] == 20  # type: ignore # noqa


def test_update_list_append(setup_dict: dict[str, SerializedObject]) -> None:
    set_nested_value_by_path(setup_dict, "attr_list[3]", MyEnum.RUNNING)
    assert setup_dict["attr_list"]["value"][3] == {  # type: ignore
        "full_access_path": "attr_list[3]",
        "doc": "MyEnum description",
        "name": "MyEnum",
        "enum": {"FINISHED": "finished", "RUNNING": "running"},
        "readonly": False,
        "type": "Enum",
        "value": "RUNNING",
    }


def test_update_invalid_list_index(
    setup_dict: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    set_nested_value_by_path(setup_dict, "attr_list[10]", 30)
    assert (
        "Error occured trying to change 'attr_list[10]': Index '10': list index out of "
        "range" in caplog.text
    )


def test_update_list_inside_class(setup_dict: dict[str, Any]) -> None:
    set_nested_value_by_path(setup_dict, "attr2.list_attr[1]", 40)
    assert setup_dict["attr2"]["value"]["list_attr"]["value"][1]["value"] == 40  # noqa


def test_update_class_attribute_inside_list(setup_dict: dict[str, Any]) -> None:
    set_nested_value_by_path(setup_dict, "attr_list[2].attr3", 50)
    assert setup_dict["attr_list"]["value"][2]["value"]["attr3"]["value"] == 50  # noqa


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


class MyService(pydase.DataService):
    name = "MyService"


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            1,
            {
                "new_attr": {
                    "full_access_path": "new_attr",
                    "type": "int",
                    "value": 1,
                    "readonly": False,
                    "doc": None,
                }
            },
        ),
        (
            1.0,
            {
                "new_attr": {
                    "full_access_path": "new_attr",
                    "type": "float",
                    "value": 1.0,
                    "readonly": False,
                    "doc": None,
                },
            },
        ),
        (
            True,
            {
                "new_attr": {
                    "full_access_path": "new_attr",
                    "type": "bool",
                    "value": True,
                    "readonly": False,
                    "doc": None,
                },
            },
        ),
        (
            u.Quantity(10, "m"),
            {
                "new_attr": {
                    "full_access_path": "new_attr",
                    "type": "Quantity",
                    "value": {"magnitude": 10, "unit": "meter"},
                    "readonly": False,
                    "doc": None,
                },
            },
        ),
        (
            MyEnum.RUNNING,
            {
                "new_attr": {
                    "full_access_path": "new_attr",
                    "value": "RUNNING",
                    "type": "Enum",
                    "doc": "MyEnum description",
                    "readonly": False,
                    "name": "MyEnum",
                    "enum": {"RUNNING": "running", "FINISHED": "finished"},
                }
            },
        ),
        (
            [1.0],
            {
                "new_attr": {
                    "full_access_path": "new_attr",
                    "value": [
                        {
                            "full_access_path": "new_attr[0]",
                            "doc": None,
                            "readonly": False,
                            "type": "float",
                            "value": 1.0,
                        }
                    ],
                    "type": "list",
                    "doc": None,
                    "readonly": False,
                }
            },
        ),
        (
            {"key": 1.0},
            {
                "new_attr": {
                    "full_access_path": "new_attr",
                    "value": {
                        "key": {
                            "full_access_path": 'new_attr["key"]',
                            "doc": None,
                            "readonly": False,
                            "type": "float",
                            "value": 1.0,
                        }
                    },
                    "type": "dict",
                    "doc": None,
                    "readonly": False,
                }
            },
        ),
        (
            MyService(),
            {
                "new_attr": {
                    "full_access_path": "new_attr",
                    "value": {
                        "name": {
                            "full_access_path": "new_attr.name",
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
                }
            },
        ),
    ],
)
def test_dynamically_add_attributes(test_input: Any, expected: dict[str, Any]) -> None:
    serialized_object: dict[str, SerializedObject] = {}

    set_nested_value_by_path(serialized_object, "new_attr", test_input)
    assert serialized_object == expected


@pytest.mark.parametrize(
    "obj, expected",
    [
        (
            service_instance.attr2,
            [
                "attr3",
                "list_attr",
                "list_attr[0]",
                "list_attr[1]",
                "some_quantity",
            ],
        ),
        (
            service_instance.dict_attr,
            [
                '["foo"]',
                '["bar"]',
                '["bar"]["foo"]',
            ],
        ),
        (
            service_instance.attr_list,
            [
                "[0]",
                "[1]",
                "[2]",
                "[2].attr3",
                "[2].list_attr",
                "[2].list_attr[0]",
                "[2].list_attr[1]",
                "[2].some_quantity",
            ],
        ),
    ],
)
def test_get_data_paths_from_serialized_object(obj: Any, expected: list[str]) -> None:
    assert get_data_paths_from_serialized_object(dump(obj=obj)) == expected


@pytest.mark.parametrize(
    "obj, expected",
    [
        (
            service_instance,
            [
                "attr1",
                "attr2",
                "attr2.attr3",
                "attr2.list_attr",
                "attr2.list_attr[0]",
                "attr2.list_attr[1]",
                "attr2.some_quantity",
                "attr_list",
                "attr_list[0]",
                "attr_list[1]",
                "attr_list[2]",
                "attr_list[2].attr3",
                "attr_list[2].list_attr",
                "attr_list[2].list_attr[0]",
                "attr_list[2].list_attr[1]",
                "attr_list[2].some_quantity",
                "dict_attr",
                'dict_attr["foo"]',
                'dict_attr["bar"]',
                'dict_attr["bar"]["foo"]',
                "enum_attr",
                "my_task",
            ],
        ),
        (
            service_instance.attr2,
            [
                "attr3",
                "list_attr",
                "list_attr[0]",
                "list_attr[1]",
                "some_quantity",
            ],
        ),
    ],
)
def test_generate_serialized_data_paths(obj: Any, expected: list[str]) -> None:
    assert generate_serialized_data_paths(dump(obj=obj)["value"]) == expected


@pytest.mark.parametrize(
    "serialized_obj, prefix, expected",
    [
        (
            {
                "full_access_path": "new_attr",
                "value": {
                    "name": {
                        "full_access_path": "new_attr.name",
                        "value": "MyService",
                    }
                },
            },
            "prefix.",
            {
                "full_access_path": "prefix.new_attr",
                "value": {
                    "name": {
                        "full_access_path": "prefix.new_attr.name",
                        "value": "MyService",
                    }
                },
            },
        ),
        (
            {
                "full_access_path": "new_attr",
                "value": [
                    {
                        "full_access_path": "new_attr[0]",
                        "value": 1.0,
                    }
                ],
            },
            "prefix.",
            {
                "full_access_path": "prefix.new_attr",
                "value": [
                    {
                        "full_access_path": "prefix.new_attr[0]",
                        "value": 1.0,
                    }
                ],
            },
        ),
        (
            {
                "full_access_path": "new_attr",
                "value": {
                    "key": {
                        "full_access_path": 'new_attr["key"]',
                        "value": 1.0,
                    }
                },
            },
            "prefix.",
            {
                "full_access_path": "prefix.new_attr",
                "value": {
                    "key": {
                        "full_access_path": 'prefix.new_attr["key"]',
                        "value": 1.0,
                    }
                },
            },
        ),
        (
            {
                "full_access_path": "new_attr",
                "value": {"magnitude": 10, "unit": "meter"},
            },
            "prefix.",
            {
                "full_access_path": "prefix.new_attr",
                "value": {"magnitude": 10, "unit": "meter"},
            },
        ),
        (
            {
                "full_access_path": "quantity_list",
                "value": [
                    {
                        "full_access_path": "quantity_list[0]",
                        "value": {"magnitude": 1.0, "unit": "A"},
                    }
                ],
            },
            "prefix.",
            {
                "full_access_path": "prefix.quantity_list",
                "value": [
                    {
                        "full_access_path": "prefix.quantity_list[0]",
                        "value": {"magnitude": 1.0, "unit": "A"},
                    }
                ],
            },
        ),
    ],
)
def test_add_prefix_to_full_access_path(
    serialized_obj: SerializedObject, prefix: str, expected: SerializedObject
) -> None:
    assert add_prefix_to_full_access_path(serialized_obj, prefix) == expected
