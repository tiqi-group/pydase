import inspect
import logging
import re
from collections.abc import Callable
from itertools import chain
from typing import Any

logger = logging.getLogger(__name__)


def parse_serialized_key(serialized_key: str) -> str | int | float:
    """
    Parse a serialized key and convert it to an appropriate type (int, float, or str).

    Args:
        serialized_key: str
            The serialized key, which might be enclosed in brackets and quotes.

    Returns:
        int | float | str:
            The processed key as an integer, float, or unquoted string.

    Examples:
        ```python
        print(parse_serialized_key("attr_name"))  # Outputs: attr_name  (str)
        print(parse_serialized_key("[123]"))  # Outputs: 123  (int)
        print(parse_serialized_key("[12.3]"))  # Outputs: 12.3  (float)
        print(parse_serialized_key("['hello']"))  # Outputs: hello  (str)
        print(parse_serialized_key('["12.34"]'))  # Outputs: 12.34  (str)
        print(parse_serialized_key('["complex"]'))  # Outputs: complex  (str)
        ```
    """

    # Strip outer brackets if present
    if serialized_key.startswith("[") and serialized_key.endswith("]"):
        serialized_key = serialized_key[1:-1]

    # Strip quotes if the resulting string is quoted
    if serialized_key.startswith(("'", '"')) and serialized_key.endswith(("'", '"')):
        return serialized_key[1:-1]

    # Try converting to float or int if the string is not quoted
    try:
        return float(serialized_key) if "." in serialized_key else int(serialized_key)
    except ValueError:
        # Return the original string if it's not a valid number
        return serialized_key


def parse_full_access_path(path: str) -> list[str]:
    """
    Splits a full access path into its atomic parts, separating attribute names, numeric
    indices (including floating points), and string keys within indices.

    Args:
        path: str
            The full access path string to be split into components.

    Returns:
        list[str]
            A list of components that make up the path, including attribute names,
            numeric indices, and string keys as separate elements.

    Example:
        >>> parse_full_access_path('dict_attr["some_key"].attr_name["other_key"]')
        ["dict_attr", '["some_key"]', "attr_name", '["other_key"]']
    """
    # Matches:
    # \w+ - Words
    # \[\d+\.\d+\] - Floating point numbers inside brackets
    # \[\d+\] - Integers inside brackets
    # \["[^"]*"\] - Double-quoted strings inside brackets
    # \['[^']*'\] - Single-quoted strings inside brackets
    pattern = r'\w+|\[\d+\.\d+\]|\[\d+\]|\["[^"]*"\]|\[\'[^\']*\']'
    return re.findall(pattern, path)


def get_path_from_path_parts(path_parts: list[str]) -> str:
    """Creates the full access path from its atomic parts.

    The reverse function is given by `parse_full_access_path`.

    Args:
        path_parts: list[str]
            A list of components that make up the path, including attribute names,
            numeric indices and string keys enclosed in square brackets as separate
            elements.
    Returns:
        str
            The full access path corresponding to the path_parts.
    """

    path = ""
    for path_part in path_parts:
        if not path_part.startswith("[") and path != "":
            path += "."
        path += path_part
    return path


def get_attribute_doc(attr: Any) -> str | None:
    """This function takes an input attribute attr and returns its documentation
    string if it's different from the documentation of its type, otherwise,
    it returns None.
    """
    attr_doc = inspect.getdoc(attr)
    attr_class_doc = inspect.getdoc(type(attr))
    return attr_doc if attr_class_doc != attr_doc else None


def get_class_and_instance_attributes(obj: object) -> dict[str, Any]:
    """Dictionary containing all attributes (both instance and class level) of a
    given object.

    If an attribute exists at both the instance and class level,the value from the
    instance attribute takes precedence.
    """

    return dict(chain(type(obj).__dict__.items(), obj.__dict__.items()))


def get_object_by_path_parts(target_obj: Any, path_parts: list[str]) -> Any:
    """Gets nested attribute of `target_object` specified by `path_parts`.

    Raises:
        AttributeError: Attribute does not exist.
        KeyError: Key in dict does not exist.
        IndexError: Index out of list range.
        TypeError: List index in the path is not a valid integer.
    """
    for part in path_parts:
        if part.startswith("["):
            deserialized_part = parse_serialized_key(part)
            target_obj = target_obj[deserialized_part]
        else:
            target_obj = getattr(target_obj, part)
    return target_obj


def get_object_attr_from_path(target_obj: Any, path: str) -> Any:
    """
    Traverse the object tree according to the given path.

    Args:
        target_obj: The root object to start the traversal from.
        path: Access path of the object.

    Returns:
        The attribute at the end of the path. If the path includes a list index,
        the function returns the specific item at that index. If an attribute in
        the path does not exist, the function logs a debug message and returns None.

    Raises:
        AttributeError: Attribute does not exist.
        KeyError: Key in dict does not exist.
        IndexError: Index out of list range.
        TypeError: List index in the path is not a valid integer.
    """
    path_parts = parse_full_access_path(path)
    return get_object_by_path_parts(target_obj, path_parts)


def get_task_class() -> type:
    from pydase.task.task import Task

    return Task


def get_component_classes() -> list[type]:
    """
    Returns references to the component classes in a list.
    """
    import pydase.components

    return [
        getattr(pydase.components, cls_name) for cls_name in pydase.components.__all__
    ]


def get_data_service_class_reference() -> Any:
    import pydase.data_service.data_service

    return getattr(pydase.data_service.data_service, "DataService")


def is_property_attribute(target_obj: Any, access_path: str) -> bool:
    path_parts = parse_full_access_path(access_path)
    target_obj = get_object_by_path_parts(target_obj, path_parts[:-1])

    # don't have to check if target_obj is dict or list as their content cannot be
    # properties -> always return False then
    return isinstance(getattr(type(target_obj), path_parts[-1], None), property)


def function_has_arguments(func: Callable[..., Any]) -> bool:
    sig = inspect.signature(func)
    parameters = dict(sig.parameters)
    # Remove 'self' parameter for instance methods.
    parameters.pop("self", None)

    # Check if there are any parameters left which would indicate additional arguments.
    return len(parameters) > 0


def is_descriptor(obj: object) -> bool:
    """Check if an object is a descriptor."""

    # Exclude functions, methods, builtins and properties
    if (
        inspect.isfunction(obj)
        or inspect.ismethod(obj)
        or inspect.isbuiltin(obj)
        or isinstance(obj, property)
    ):
        return False

    # Check if it has any descriptor methods
    return any(hasattr(obj, method) for method in ("__get__", "__set__", "__delete__"))


def current_event_loop_exists() -> bool:
    """Check if a running and open asyncio event loop exists in the current thread.

    This checks if an event loop is set via the current event loop policy and verifies
    that the loop has not been closed.

    Returns:
        True if an event loop exists and is not closed, False otherwise.
    """

    import asyncio

    try:
        return not asyncio.get_event_loop().is_closed()
    except RuntimeError:
        return False
