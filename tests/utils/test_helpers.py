from typing import Any

import pydase
import pytest
from pydase.utils.helpers import (
    get_object_by_path_parts,
    get_path_from_path_parts,
    is_property_attribute,
    parse_full_access_path,
    parse_serialized_key,
)


@pytest.mark.parametrize(
    "serialized_key, expected",
    [
        ("attr_name", "attr_name"),
        ("[0]", 0),
        ("[0.0]", 0.0),
        ('["some_key"]', "some_key"),
        ('["12.34"]', "12.34"),
    ],
)
def test_parse_serialized_key(serialized_key: str, expected: str) -> None:
    assert parse_serialized_key(serialized_key) == expected


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
        ("dict_attr[2.1]", ["dict_attr", "[2.1]"]),
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
        (["dict_attr", "[2.1]"], "dict_attr[2.1]"),
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
        self.dict_attr = {"foo": SubService(), 2.1: "float_as_key"}


service_instance = MyService()


@pytest.mark.parametrize(
    "path_parts, expected",
    [
        (["some_float"], service_instance.some_float),
        (["subservice"], service_instance.subservice),
        (["list_attr", "[0]"], service_instance.list_attr[0]),
        (["list_attr", "[1]"], service_instance.list_attr[1]),
        (["dict_attr", '["foo"]'], service_instance.dict_attr["foo"]),
        (["dict_attr", '["foo"]', "name"], service_instance.dict_attr["foo"].name),  # type: ignore
        (["dict_attr", "[2.1]"], service_instance.dict_attr[2.1]),
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
        ("nested_class_instance", False),
        ("nested_class_instance.my_property", True),
        ("list_attr", False),
        ("list_attr[0]", False),
        ("list_attr[0].my_property", True),
        ("dict_attr", False),
        ("dict_attr['foo']", False),
        ("dict_attr['foo'].my_property", True),
    ],
)
def test_is_property_attribute(attr_name: str, expected: bool) -> None:
    class NestedClass:
        @property
        def my_property(self) -> str:
            return "I'm a nested property"

    # Test Suite
    class DummyClass:
        def __init__(self) -> None:
            self.regular_attribute = "I'm just an attribute"
            self.nested_class_instance = NestedClass()
            self.list_attr = [NestedClass()]
            self.dict_attr = {"foo": NestedClass()}

        @property
        def my_property(self) -> str:
            return "I'm a property"

        def my_method(self) -> str:
            return "I'm a method"

    dummy = DummyClass()
    assert is_property_attribute(dummy, attr_name) == expected
