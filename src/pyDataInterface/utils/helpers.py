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


def get_DataService_attr_from_path(target_obj: Any, path: list[str]) -> Any:
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
        # Skip the root object itself
        if part == "DataService":
            continue

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


def generate_paths_and_values_from_serialized_DataService(
    data: dict,
) -> dict[str, Any]:
    """
    Recursively generate paths from a dictionary and return a dictionary of paths and
    their corresponding values.

    This function traverses through a nested dictionary (usually the result of a
    serialization of a DataService) and generates a dictionary where the keys are the
    paths to each terminal value in the original dictionary and the values are the
    corresponding terminal values in the original dictionary.

    The paths are represented as string keys with dots connecting the levels and
    brackets indicating list indices.

    Args:
        data (dict): The input dictionary to generate paths and values from.
        parent_path (Optional[str], optional): The current path up to the current level
        of recursion. Defaults to None.

    Returns:
        dict[str, Any]: A dictionary with paths as keys and corresponding values as
        values.
    """

    paths_and_values = {}
    for key, value in data.items():
        if value["type"] == "method":
            # ignoring methods
            continue
        if isinstance(value["value"], dict):
            paths_and_values[
                key
            ] = generate_paths_and_values_from_serialized_DataService(value["value"])

        elif isinstance(value["value"], list):
            for index, item in enumerate(value["value"]):
                indexed_key_path = f"{key}[{index}]"
                if isinstance(item["value"], dict):
                    paths_and_values[
                        indexed_key_path
                    ] = generate_paths_and_values_from_serialized_DataService(
                        item["value"]
                    )
                else:
                    paths_and_values[indexed_key_path] = item["value"]  # type: ignore
        else:
            paths_and_values[key] = value["value"]  # type: ignore
    return paths_and_values


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


def set_if_differs(target: Any, attr_name: str | int, new_value: Any) -> None:
    """
    Set the value of an attribute or a list element on a target object to a new value,
    but only if the current value of the attribute or the list element differs from the
    new value.

    Args:
        target: The object that has the attribute or the list.
        attr_name: The name of the attribute or the index of the list element.
        new_value: The new value for the attribute or the list element.
    """
    if isinstance(target, list) and isinstance(attr_name, int):
        # Case for a list
        if target[attr_name] != new_value:
            target[attr_name] = new_value
    elif isinstance(attr_name, str):
        # Case for an attribute
        if getattr(target, attr_name) != new_value:
            setattr(target, attr_name, new_value)
    else:
        logger.error(f"Incompatible arguments: {target}, {attr_name}.")
