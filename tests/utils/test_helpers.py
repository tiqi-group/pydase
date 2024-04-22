from typing import Any

import pytest
from pydase.utils.helpers import (
    is_property_attribute,
    parse_keyed_attribute,
)


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


@pytest.mark.parametrize(
    "attr_name, expected",
    [
        ("attr_name", ("attr_name", None)),
        ("list_attr[2]", ("list_attr", 2)),
        ('dict_attr["2"]', ("dict_attr", "2")),
        ('dict_attr["some_key"]', ("dict_attr", "some_key")),
        ("dict_attr[2]", ("dict_attr", 2)),
        ("dict_attr[2.1]", ("dict_attr", 2.1)),
    ],
)
def test_parse_keyed_attributes(attr_name: str, expected: tuple[str, Any]) -> None:
    assert parse_keyed_attribute(attr_name) == expected
