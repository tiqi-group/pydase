import inspect
import logging
from itertools import chain
from typing import Any

logger = logging.getLogger(__name__)


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


def get_object_attr_from_path_list(target_obj: Any, path: list[str]) -> Any:
    """
    Traverse the object tree according to the given path.

    Args:
        target_obj: The root object to start the traversal from.
        path: A list of attribute names representing the path to traverse.

    Returns:
        The attribute at the end of the path. If the path includes a list index,
        the function returns the specific item at that index. If an attribute in
        the path does not exist, the function logs a debug message and returns None.

    Raises:
        ValueError: If a list index in the path is not a valid integer.
    """
    for part in path:
        try:
            # Try to split the part into attribute and index
            attr, index_str = part.split("[", maxsplit=1)
            index_str = index_str.replace("]", "")
            index = int(index_str)
            target_obj = getattr(target_obj, attr)[index]
        except ValueError:
            # No index, so just get the attribute
            target_obj = getattr(target_obj, part)
        except AttributeError:
            # The attribute doesn't exist
            logger.debug("Attribute % does not exist in the object.", part)
            return None
    return target_obj


def convert_arguments_to_hinted_types(
    args: dict[str, Any], type_hints: dict[str, Any]
) -> dict[str, Any] | str:
    """
    Convert the given arguments to their types hinted in the type_hints dictionary.

    This function attempts to convert each argument in the args dictionary to the type
    specified for the argument in the type_hints dictionary. If the conversion is
    successful, the function replaces the original argument in the args dictionary with
    the converted argument.

    If a ValueError is raised during the conversion of an argument, the function logs
    an error message and returns the error message as a string.

    Args:
        args: A dictionary of arguments to be converted. The keys are argument names
              and the values are the arguments themselves.
        type_hints: A dictionary of type hints for the arguments. The keys are
                    argument names and the values are the hinted types.

    Returns:
        A dictionary of the converted arguments if all conversions are successful,
        or an error message string if a ValueError is raised during a conversion.
    """

    # Convert arguments to their hinted types
    for arg_name, arg_value in args.items():
        if arg_name in type_hints:
            arg_type = type_hints[arg_name]
            if isinstance(arg_type, type):
                # Attempt to convert the argument to its hinted type
                try:
                    args[arg_name] = arg_type(arg_value)
                except ValueError:
                    msg = (
                        f"Failed to convert argument '{arg_name}' to type "
                        f"{arg_type.__name__}"
                    )
                    logger.error(msg)
                    return msg
    return args


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


def parse_list_attr_and_index(attr_string: str) -> tuple[str, int | None]:
    """
    Parses an attribute string and extracts a potential list attribute name and its
    index.
    Logs an error if the index is not a valid digit.

    Args:
        attr_string (str):
            The attribute string to parse. Can be a regular attribute name (e.g.,
            'attr_name') or a list attribute with an index (e.g., 'list_attr[2]').

    Returns:
        tuple[str, Optional[int]]:
            A tuple containing the attribute name as a string and the index as an
            integer if present, otherwise None.

    Examples:
        >>> parse_attribute_and_index('list_attr[2]')
        ('list_attr', 2)
        >>> parse_attribute_and_index('attr_name')
        ('attr_name', None)
    """

    index = None
    attr_name = attr_string
    if "[" in attr_string and attr_string.endswith("]"):
        attr_name, index_part = attr_string.split("[", 1)
        index_part = index_part.rstrip("]")
        if index_part.isdigit():
            index = int(index_part)
        else:
            logger.error("Invalid index format in key: %s", attr_name)
    return attr_name, index


def get_component_class_names() -> list[str]:
    """
    Returns the names of the component classes in a list.

    It takes the names from the pydase/components/__init__.py file, so this file should
    always be up-to-date with the currently available components.

    Returns:
        list[str]: List of component class names
    """
    import pydase.components

    return pydase.components.__all__


def is_property_attribute(target_obj: Any, attr_name: str) -> bool:
    return isinstance(getattr(type(target_obj), attr_name, None), property)
