import re
from itertools import chain
from typing import Any

from loguru import logger


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


def get_attr_from_path(target_obj: Any, path: list[str]) -> Any:
    """
    Traverse the object tree according to the given path.

    Args:
        target_obj: The root object to start the traversal from.
        path: A list of attribute names representing the path to traverse.

    Returns:
        The attribute at the end of the path. If the path includes a list index,
        the function returns the specific item at that index.

    Raises:
        ValueError: If a list index in the path is not a valid integer.
    """
    for part in path:
        if part != "DataService":  # Skip the root object itself
            # Check if part contains an index for a list item
            if re.search(r"\[.*\]", part):
                attr, index_str = part.split("[")
                try:
                    index = int(
                        index_str.replace("]", "")
                    )  # Remove closing bracket and convert to int
                except ValueError:
                    logger.error(f"Invalid list index: {index_str}")
                    raise ValueError(f"Invalid list index: {index_str}")
                target_obj = getattr(target_obj, attr)[index]
            else:
                target_obj = getattr(target_obj, part)
    return target_obj
