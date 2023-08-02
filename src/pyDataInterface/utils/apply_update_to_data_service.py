import re
from enum import Enum
from typing import Any, Optional, TypedDict, get_type_hints

from loguru import logger

from pyDataInterface.data_service.data_service import DataService

from .helpers import get_attr_from_path


class UpdateDictionary(TypedDict):
    name: str
    """Name of the attribute."""
    parent_path: str
    """Full access path of the attribute."""
    value: Any
    """New value of the attribute."""


def apply_updates_to_data_service(service: Any, data: UpdateDictionary) -> Any:
    parent_path = data["parent_path"].split(".")
    attr_name = data["name"]

    # Traverse the object tree according to parent_path
    target_obj = get_attr_from_path(service, parent_path)

    # Check if attr_name contains an index for a list item
    index: Optional[int] = None
    if re.search(r"\[.*\]", attr_name):
        attr_name, index_str = attr_name.split("[")
        try:
            index = int(
                index_str.replace("]", "")
            )  # Remove closing bracket and convert to int
        except ValueError:
            logger.error(f"Invalid list index: {index_str}")
            return

    attr = getattr(target_obj, attr_name)

    if isinstance(attr, DataService):
        attr.apply_updates(data["value"])
    elif isinstance(attr, Enum):
        setattr(service, data["name"], attr.__class__[data["value"]["value"]])
    elif callable(attr):
        args: dict[str, Any] = data["value"]["args"]
        type_hints = get_type_hints(attr)

        # Convert arguments to their hinted types
        for arg_name, arg_value in args.items():
            if arg_name in type_hints:
                arg_type = type_hints[arg_name]
                if isinstance(arg_type, type):
                    # Attempt to convert the argument to its hinted type
                    try:
                        args[arg_name] = arg_type(arg_value)
                    except ValueError:
                        msg = f"Failed to convert argument '{arg_name}' to type {arg_type.__name__}"
                        logger.error(msg)
                        return msg

        return attr(**args)
    elif isinstance(attr, list):
        attr[index] = data["value"]
    else:
        setattr(target_obj, attr_name, data["value"])
