from typing import Any

import pydase
import pytest
from pydase.utils.helpers import (
    get_object_attr_from_path,
    get_object_by_path_parts,
    get_path_from_path_parts,
    is_property_attribute,
    parse_full_access_path,
)


@pytest.mark.parametrize(
    "full_access_path, expected",
    [
        ("attr_name", ["attr_name"]),
        ("parent.attr_name", ["parent", "attr_name"]),
        ("nested.parent.attr_name", ["nested", "parent", "attr_name"]),
        ("nested.parent.attr_name", ["nested", "parent", "attr_name"]),
        ("attr_name[0]", ["attr_name", "[0]"]),
        ("parent.attr_name[0]", ["parent", "attr_name", "[0]"]),
        ("attr_name[0][1]", ["attr_name", "[0]", "[1]"]),
        ('attr_name[0]["some_key"]', ["attr_name", "[0]", '["some_key"]']),
        (
            'dict_attr["some_key"].attr_name["other_key"]',
            ["dict_attr", '["some_key"]', "attr_name", '["other_key"]'],
        ),
    ],
)
def test_parse_full_access_path(full_access_path: str, expected: list[str]) -> None:
    assert parse_full_access_path(full_access_path) == expected


@pytest.mark.parametrize(
    "path_parts, expected",
    [
        (["attr_name"], "attr_name"),
        (["parent", "attr_name"], "parent.attr_name"),
        (["nested", "parent", "attr_name"], "nested.parent.attr_name"),
        (["nested", "parent", "attr_name"], "nested.parent.attr_name"),
        (["attr_name", "[0]"], "attr_name[0]"),
        (["parent", "attr_name", "[0]"], "parent.attr_name[0]"),
        (["attr_name", "[0]", "[1]"], "attr_name[0][1]"),
        (["attr_name", "[0]", '["some_key"]'], 'attr_name[0]["some_key"]'),
        (
            ["dict_attr", '["some_key"]', "attr_name", '["other_key"]'],
            'dict_attr["some_key"].attr_name["other_key"]',
        ),
    ],
)
def test_get_path_from_path_parts(path_parts: list[str], expected: str) -> None:
    assert get_path_from_path_parts(path_parts) == expected


class SubService(pydase.DataService):
    name = "SubService"
    some_int = 1
    some_float = 1.0


class MyService(pydase.DataService):
    def __init__(self) -> None:
        super().__init__()
        self.some_float = 1.0
        self.subservice = SubService()
        self.list_attr = [1.0, SubService()]
        self.dict_attr = {"foo": SubService()}


service_instance = MyService()


@pytest.mark.parametrize(
    "path_parts, expected",
    [
        (["some_float"], service_instance.some_float),
        (["subservice"], service_instance.subservice),
        (["list_attr", "[0]"], service_instance.list_attr[0]),
        (["list_attr", "[1]"], service_instance.list_attr[1]),
        (["dict_attr", '["foo"]'], service_instance.dict_attr["foo"]),
        (["dict_attr", '["foo"]', "name"], service_instance.dict_attr["foo"].name),
    ],
)
def test_get_object_by_path_parts(path_parts: list[str], expected: Any) -> None:
    assert get_object_by_path_parts(service_instance, path_parts) == expected


@pytest.mark.parametrize(
    "attr_name, expected",
    [
        ("regular_attribute", False),
        ("my_property", True),
        ("my_method", False),
        ("non_existent_attr", False),
    ],
)
def test_is_property_attribute(attr_name: str, expected: bool) -> None:
    # Test Suite
    class DummyClass:
        def __init__(self) -> None:
            self.regular_attribute = "I'm just an attribute"

        @property
        def my_property(self) -> str:
            return "I'm a property"

        def my_method(self) -> str:
            return "I'm a method"

    dummy = DummyClass()
    assert is_property_attribute(dummy, attr_name) == expected


def test_get_object_attr_from_path() -> None:
    class SubService(pydase.DataService):
        name = "SubService"
        some_int = 1
        some_float = 1.0

    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.some_float = 1.0
            self.subservice = SubService()
            self.list_attr = [1.0, SubService()]
            self.dict_attr = {"foo": SubService()}

    service_instance = MyService()

    for attr_name, obj in [
        ("some_float", service_instance.some_float),
        ("subservice", service_instance.subservice),
        ("list_attr[0]", service_instance.list_attr[0]),
        ("list_attr[1]", service_instance.list_attr[1]),
        ("dict_attr['foo']", service_instance.dict_attr["foo"]),
    ]:
        assert get_object_attr_from_path(service_instance, attr_name) == obj


# def test_get_nested_dict_by_path() -> None:
#     obj = {"2.1": "foo", 2.1: "bar"}
#     serialized_object = {
#         "dict_attr": dump(obj=obj),
#     }
#     assert get_nested_dict_by_path(serialized_object, 'dict_attr["2.1"]') == {}
