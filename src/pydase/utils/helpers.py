import inspect
import logging
import re
from collections.abc import Callable
from itertools import chain
from typing import Any

logger = logging.getLogger(__name__)


def parse_full_access_path(path: str) -> list[str]:
    """
    Splits a full access path into its atomic parts, separating attribute names, numeric
    indices, and string keys within indices.

    The reverse function is given by `get_path_from_path_parts`.

    Args:
        path: str
            The full access path string to be split into components.

    Returns:
        list[str]
            A list of components that make up the path, including attribute names,
            numeric indices, and string keys as separate elements.
    """
    # <word_with_underscore> | [<any number of digits>]
    #                        | ["<anything except ">"]
    #                        | ['<anything except '>']
    pattern = r'\w+|\[\d+\]|\["[^"]*"\]|\[\'[^\']*\']'
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
    The __root__ object is removed as this will lead to endless recursion in the for
    loops.
    """

    return dict(chain(type(obj).__dict__.items(), obj.__dict__.items()))


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
        ValueError: If a list index in the path is not a valid integer.
    """
    path_list = path.split(".") if path != "" else []
    for part in path_list:
        attr, key = parse_keyed_attribute(part)
        try:
            if key is not None:
                target_obj = getattr(target_obj, attr)[key]
            else:
                target_obj = getattr(target_obj, attr)
        except AttributeError:
            # The attribute doesn't exist
            logger.debug("Attribute % does not exist in the object.", part)
            return None
    return target_obj


def update_value_if_changed(
    target: Any, attr_name_or_index: str | int, new_value: Any
) -> None:
    """
    Updates the value of an attribute or a list element on a target object if the new
    value differs from the current one.

    This function supports updating both attributes of an object and elements of a list.

    - For objects, the function first checks the current value of the attribute. If the
      current value differs from the new value, the function updates the attribute.

    - For lists, the function checks the current value at the specified index. If the
      current value differs from the new value, the function updates the list element
      at the given index.

    Args:
        target (Any):
            The target object that has the attribute or the list.
        attr_name_or_index (str | int):
            The name of the attribute or the index of the list element.
        new_value (Any):
            The new value for the attribute or the list element.
    """

    if isinstance(target, list) and isinstance(attr_name_or_index, int):
        if target[attr_name_or_index] != new_value:
            target[attr_name_or_index] = new_value
    elif isinstance(attr_name_or_index, str):
        # If the type matches and the current value is different from the new value,
        # update the attribute.
        if getattr(target, attr_name_or_index) != new_value:
            setattr(target, attr_name_or_index, new_value)
    else:
        logger.error("Incompatible arguments: %s, %s.", target, attr_name_or_index)


def parse_keyed_attribute(attr_string: str) -> tuple[str, str | float | int | None]:
    """
    Parses an attribute string and extracts a potential attribute name and its key.
    The key can be a string (for dictionary keys) or an integer (for list indices).

    Args:
        attr_string (str):
            The attribute string to parse. Can be a regular attribute name (e.g.,
            'attr_name'), a list attribute with an index (e.g., 'list_attr[2]'), or
            a dictionary attribute with a key (e.g., 'dict_attr["key"]' or
            'dict_attr[0]').

    Returns:
        tuple[str, str | float | int | None]:
            A tuple containing the attribute name and the key as either a string,
            an integer if it's a digit, or None if no key is present.

    Examples:
        ```python
        >>> parse_keyed_attribute('list_attr[2]')
        ("list_attr", 2)
        >>> parse_keyed_attribute('attr_name')
        ("attr_name", None)
        >>> parse_keyed_attribute('dict_attr["key"]')
        ("dict_attr", "key")
        >>> parse_keyed_attribute("dict_attr['key']")
        ("dict_attr", "key")
        >>> parse_keyed_attribute("dict_attr["0"]")
        ("dict_attr", "0")
        >>> parse_keyed_attribute("dict_attr[0]")
        ("dict_attr", 0)
        ```
    """

    key: str | float | int | None = None
    attr_name = attr_string
    if "[" in attr_string and attr_string.endswith("]"):
        attr_name, key_part = attr_string.split("[", 1)
        key_part = key_part.rstrip("]")
        # Remove quotes if present (supports both single and double quotes)
        if key_part.startswith(('"', "'")) and key_part.endswith(('"', "'")):
            key = key_part[1:-1]
        elif "." in key_part:
            key = float(key_part)
        else:
            key = int(key_part)
    return attr_name, key


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
    parent_path, attr_name = (
        ".".join(access_path.split(".")[:-1]),
        access_path.split(".")[-1],
    )
    target_obj = get_object_attr_from_path(target_obj, parent_path)
    return isinstance(getattr(type(target_obj), attr_name, None), property)


def function_has_arguments(func: Callable[..., Any]) -> bool:
    sig = inspect.signature(func)
    parameters = dict(sig.parameters)
    # Remove 'self' parameter for instance methods.
    parameters.pop("self", None)

    # Check if there are any parameters left which would indicate additional arguments.
    if len(parameters) > 0:
        return True
    return False


def render_in_frontend(func: Callable[..., Any]) -> bool:
    """Determines if the method should be rendered in the frontend.

    It checks if the "@frontend" decorator was used or the method is a coroutine."""

    if inspect.iscoroutinefunction(func):
        return True

    try:
        return func._display_in_frontend  # type: ignore
    except AttributeError:
        return False
