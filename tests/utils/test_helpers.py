import pytest

from pydase.utils.helpers import (
    extract_dict_or_list_entry,
    get_nested_value_from_DataService_by_path_and_key,
    is_property_attribute,
)

# Sample data for the tests
data_sample = {
    "attr1": {"type": "bool", "value": False, "readonly": False, "doc": None},
    "class_attr": {
        "type": "MyClass",
        "value": {"sub_attr": {"type": "float", "value": 20.5}},
    },
    "list_attr": {
        "type": "list",
        "value": [
            {"type": "int", "value": 0, "readonly": False, "doc": None},
            {"type": "float", "value": 1.0, "readonly": False, "doc": None},
        ],
        "readonly": False,
    },
}


# Tests for extract_dict_or_list_entry
def test_extract_dict_with_valid_list_index() -> None:
    result = extract_dict_or_list_entry(data_sample, "list_attr[1]")
    assert result == {"type": "float", "value": 1.0, "readonly": False, "doc": None}


def test_extract_dict_without_list_index() -> None:
    result = extract_dict_or_list_entry(data_sample, "attr1")
    assert result == {"type": "bool", "value": False, "readonly": False, "doc": None}


def test_extract_dict_with_invalid_key() -> None:
    result = extract_dict_or_list_entry(data_sample, "attr_not_exist")
    assert result is None


def test_extract_dict_with_invalid_list_index() -> None:
    result = extract_dict_or_list_entry(data_sample, "list_attr[5]")
    assert result is None


# Tests for get_nested_value_from_DataService_by_path_and_key
def test_get_nested_value_with_default_key() -> None:
    result = get_nested_value_from_DataService_by_path_and_key(
        data_sample, "list_attr[0]"
    )
    assert result == 0


def test_get_nested_value_with_custom_key() -> None:
    result = get_nested_value_from_DataService_by_path_and_key(
        data_sample, "class_attr.sub_attr", "type"
    )
    assert result == "float"


def test_get_nested_value_with_invalid_path() -> None:
    result = get_nested_value_from_DataService_by_path_and_key(
        data_sample, "class_attr.nonexistent_attr"
    )
    assert result is None


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
