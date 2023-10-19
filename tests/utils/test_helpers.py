import tempfile
from pathlib import Path

import pytest
from pydase.utils.helpers import (
    create_config_folder,
    is_property_attribute,
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


def test_create_config_folder() -> None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        print("created temporary directory", tmpdirname)

        config_dir = Path(tmpdirname) / "config"

        assert not config_dir.exists()

        create_config_folder(config_dir)

        assert config_dir.exists()

        # Call the function again to test idempotency (it should not fail if the
        # directory already exists)
        create_config_folder(config_dir)
