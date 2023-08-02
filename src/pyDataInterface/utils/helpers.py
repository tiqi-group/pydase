from itertools import chain
from typing import Any


def get_class_and_instance_attributes(obj: object) -> dict[str, Any]:
    """Dictionary containing all attributes (both instance and class level) of a
    given object.

    If an attribute exists at both the instance and class level,the value from the
    instance attribute takes precedence.
    The __root__ object is removed as this will lead to endless recursion in the for
    loops.
    """

    attrs = dict(chain(type(obj).__dict__.items(), obj.__dict__.items()))
    attrs.pop("__root__")
    return attrs
