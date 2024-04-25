import inspect
import logging
import re
from collections.abc import Callable
from itertools import chain
from typing import Any

logger = logging.getLogger(__name__)


def parse_serialized_key(serialized_key: str) -> str | int | float:
    processed_key: int | float | str = serialized_key
    if serialized_key.startswith("["):
        assert serialized_key.endswith("]")
        processed_key = serialized_key[1:-1]
        if '"' in processed_key or "'" in processed_key:
            processed_key = processed_key[1:-1]
        elif "." in processed_key:
            processed_key = float(processed_key)
        else:
            processed_key = int(processed_key)

    return processed_key


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


def get_object_by_path_parts(target_obj: Any, path_parts: list[str]) -> Any:
    for part in path_parts:
        if part.startswith("["):
            deserialized_part = parse_serialized_key(part)
            target_obj = target_obj[deserialized_part]
        else:
            try:
                target_obj = getattr(target_obj, part)
            except AttributeError:
                logger.debug("Attribute % does not exist in the object.", part)
                return None
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
        ValueError: If a list index in the path is not a valid integer.
    """
    path_parts = parse_full_access_path(path)
    return get_object_by_path_parts(target_obj, path_parts)


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
