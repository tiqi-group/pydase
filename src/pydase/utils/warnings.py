from loguru import logger


def warn_if_instance_class_does_not_inherit_from_DataService(__value: object) -> None:
    base_class_name = __value.__class__.__base__.__name__
    module_name = __value.__class__.__module__

    if (
        module_name
        not in [
            "builtins",
            "__builtin__",
            "asyncio.unix_events",
            "_abc",
        ]
        and base_class_name not in ["DataService", "list", "Enum"]
        and type(__value).__name__ not in ["CallbackManager", "TaskManager", "Quantity"]
    ):
        logger.warning(
            f"Warning: Class {type(__value).__name__} does not inherit from DataService."
        )
