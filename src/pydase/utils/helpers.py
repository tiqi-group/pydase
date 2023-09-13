import re
from itertools import chain
from typing import Any, Optional, cast

from loguru import logger

STANDARD_TYPES = ("int", "float", "bool", "str", "Enum", "NoneType", "Quantity")


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


def get_object_attr_from_path(target_obj: Any, path: list[str]) -> Any:
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
            logger.debug(f"Attribute {part} does not exist in the object.")
            return None
    return target_obj


def generate_paths_from_DataService_dict(
    data: dict, parent_path: str = ""
) -> list[str]:
    """
    Recursively generate paths from a dictionary representing a DataService object.

    This function traverses through a nested dictionary, which is typically obtained
    from serializing a DataService object. The function generates a list where each
    element is a string representing the path to each terminal value in the original
    dictionary.

    The paths are represented as strings, with dots ('.') denoting nesting levels and
    square brackets ('[]') denoting list indices.

    Args:
        data (dict): The input dictionary to generate paths from. This is typically
        obtained from serializing a DataService object.
        parent_path (str, optional): The current path up to the current level of
        recursion. Defaults to ''.

    Returns:
        list[str]: A list with paths as elements.

    Note:
        The function ignores keys whose "type" is "method", as these represent methods
        of the DataService object and not its state.

    Example:
    -------

    >>> {
    ...     "attr1": {"type": "int", "value": 10},
    ...     "attr2": {
    ...         "type": "list",
    ...         "value": [{"type": "int", "value": 1}, {"type": "int", "value": 2}],
    ...     },
    ...     "add": {
    ...         "type": "method",
    ...         "async": False,
    ...         "parameters": {"a": "float", "b": "int"},
    ...         "doc": "Returns the sum of the numbers a and b.",
    ...     },
    ... }
    >>> print(generate_paths_from_DataService_dict(nested_dict))
    [attr1, attr2[0], attr2[1]]
    """

    paths = []
    for key, value in data.items():
        if value["type"] == "method":
            # ignoring methods
            continue
        new_path = f"{parent_path}.{key}" if parent_path else key
        if isinstance(value["value"], dict) and value["type"] != "Quantity":
            paths.extend(generate_paths_from_DataService_dict(value["value"], new_path))  # type: ignore
        elif isinstance(value["value"], list):
            for index, item in enumerate(value["value"]):
                indexed_key_path = f"{new_path}[{index}]"
                if isinstance(item["value"], dict):
                    paths.extend(  # type: ignore
                        generate_paths_from_DataService_dict(
                            item["value"], indexed_key_path
                        )
                    )
                else:
                    paths.append(indexed_key_path)  # type: ignore
        else:
            paths.append(new_path)  # type: ignore
    return paths


def extract_dict_or_list_entry(data: dict[str, Any], key: str) -> dict[str, Any] | None:
    """
    Extract a nested dictionary or list entry based on the provided key.

    Given a dictionary and a key, this function retrieves the corresponding nested
    dictionary or list entry. If the key includes an index in the format "[<index>]",
    the function assumes that the corresponding entry in the dictionary is a list, and
    it will attempt to retrieve the indexed item from that list.

    Args:
        data (dict): The input dictionary containing nested dictionaries or lists.
        key (str): The key specifying the desired entry within the dictionary. The key
            can be a regular dictionary key or can include an index in the format
            "[<index>]" to retrieve an item from a nested list.

    Returns:
        dict | None: The nested dictionary or list item found for the given key. If the
            key is invalid, or if the specified index is out of bounds for a list, it
            returns None.

    Example:
        >>> data = {
        ...     "attr1": [
        ...         {"type": "int", "value": 10}, {"type": "string", "value": "hello"}
        ...     ],
        ...     "attr2": {
        ...         "type": "MyClass",
        ...         "value": {"sub_attr": {"type": "float", "value": 20.5}}
        ...     }
        ... }

        >>> extract_dict_or_list_entry(data, "attr1[1]")
        {"type": "string", "value": "hello"}

        >>> extract_dict_or_list_entry(data, "attr2")
        {"type": "MyClass", "value": {"sub_attr": {"type": "float", "value": 20.5}}}
    """

    attr_name = key
    index: Optional[int] = None

    # Check if the key contains an index part like '[<index>]'
    if "[" in key and key.endswith("]"):
        attr_name, index_part = key.split("[", 1)
        index_part = index_part.rstrip("]")  # remove the closing bracket

        # Convert the index part to an integer
        if index_part.isdigit():
            index = int(index_part)
        else:
            logger.error(f"Invalid index format in key: {key}")

    current_data: dict[str, Any] | list[dict[str, Any]] | None = data.get(
        attr_name, None
    )
    if not isinstance(current_data, dict):
        # key does not exist in dictionary, e.g. when class does not have this
        # attribute
        return None

    if isinstance(current_data["value"], list):
        current_data = current_data["value"]

        if index is not None and 0 <= index < len(current_data):
            current_data = current_data[index]
        else:
            return None

    # When the attribute is a class instance, the attributes are nested in the
    # "value" key
    if current_data["type"] not in STANDARD_TYPES:
        current_data = cast(dict[str, Any], current_data.get("value", None))  # type: ignore
        assert isinstance(current_data, dict)

    return current_data


def get_nested_value_from_DataService_by_path_and_key(
    data: dict[str, Any], path: str, key: str = "value"
) -> Any:
    """
    Get the value associated with a specific key from a dictionary given a path.

    This function traverses the dictionary according to the path provided and
    returns the value associated with the specified key at that path. The path is
    a string with dots connecting the levels and brackets indicating list indices.

    The function can handle complex dictionaries where data is nested within different
    types of objects. It checks the type of each object it encounters and correctly
    descends into the object if it is not a standard type (i.e., int, float, bool, str,
    Enum).

    Args:
        data (dict): The input dictionary to get the value from.
        path (str): The path to the value in the dictionary.
        key (str, optional): The key associated with the value to be returned.
                             Default is "value".

    Returns:
        Any: The value associated with the specified key at the given path in the
        dictionary.

    Examples:
        Let's consider the following dictionary:

        >>> data = {
        >>>     "attr1": {"type": "int", "value": 10},
        >>>     "attr2": {
                    "type": "MyClass",
                    "value": {"attr3": {"type": "float", "value": 20.5}}
                }
        >>> }

        The function can be used to get the value of 'attr1' as follows:
        >>> get_nested_value_by_path_and_key(data, "attr1")
        10

        It can also be used to get the value of 'attr3', which is nested within 'attr2',
        as follows:
        >>> get_nested_value_by_path_and_key(data, "attr2.attr3", "type")
        float
    """

    # Split the path into parts
    parts: list[str] = re.split(r"\.", path)  # Split by '.'
    current_data: dict[str, Any] | None = data

    for part in parts:
        if current_data is None:
            return
        current_data = extract_dict_or_list_entry(current_data, part)

    if isinstance(current_data, dict):
        return current_data.get(key, None)


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
        logger.error(f"Incompatible arguments: {target}, {attr_name_or_index}.")


def parse_list_attr_and_index(attr_string: str) -> tuple[str, Optional[int]]:
    """
    Parses an attribute string and extracts a potential list attribute name and its
    index.

    This function examines the provided attribute string. If the string contains square
    brackets, it assumes that it's a list attribute and the string within brackets is
    the index of an element. It then returns the attribute name and the index as an
    integer. If no brackets are present, the function assumes it's a regular attribute
    and returns the attribute name and None as the index.

    Parameters:
    -----------
    attr_string: str
        The attribute string to parse. Can be a regular attribute name (e.g.
        'attr_name') or a list attribute with an index (e.g. 'list_attr[2]').

    Returns:
    --------
    tuple: (str, Optional[int])
        A tuple containing the attribute name as a string and the index as an integer if
        present, otherwise None.

    Example:
    --------
    >>> parse_list_attr_and_index('list_attr[2]')
    ('list_attr', 2)
    >>> parse_list_attr_and_index('attr_name')
    ('attr_name', None)
    """

    attr_name = attr_string
    index = None
    if "[" in attr_string and "]" in attr_string:
        attr_name, idx = attr_string[:-1].split("[")
        index = int(idx)
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
