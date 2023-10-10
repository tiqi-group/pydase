from enum import Enum

import pydase


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

    assert EnumAttribute().serialize() == {
        "some_enum": {
            "type": "Enum",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": False,
            "doc": None,
        }
    }
    assert EnumPropertyWithoutSetter().serialize() == {
        "some_enum": {
            "type": "Enum",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": True,
            "doc": None,
        }
    }
    assert EnumPropertyWithSetter().serialize() == {
        "some_enum": {
            "type": "Enum",
            "value": "FOO",
            "enum": {"FOO": "foo", "BAR": "bar"},
            "readonly": False,
            "doc": None,
        }
    }
