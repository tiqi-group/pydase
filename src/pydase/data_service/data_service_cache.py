import logging
from typing import TYPE_CHECKING, Any

from pydase.utils.helpers import set_nested_value_in_dict

if TYPE_CHECKING:
    from pydase import DataService

logger = logging.getLogger(__name__)


class DataServiceCache:
    def __init__(self, service: "DataService") -> None:
        self._cache: dict[str, Any] = {}
        self.service = service
        self._cache_initialized = False

    @property
    def cache(self) -> dict[str, Any]:
        """Property to lazily initialize the cache."""
        if not self._cache_initialized:
            self._initialize_cache()
        return self._cache

    def _initialize_cache(self) -> None:
        """Initializes the cache and sets up the callback."""
        logger.debug("Initializing cache.")
        self._cache = self.service.serialize()
        self.service._callback_manager.add_notification_callback(self.update_cache)
        self._cache_initialized = True

    def update_cache(self, parent_path: str, name: str, value: Any) -> None:
        # Remove the part before the first "." in the parent_path
        parent_path = ".".join(parent_path.split(".")[1:])

        # Construct the full path
        full_path = f"{parent_path}.{name}" if parent_path else name

        set_nested_value_in_dict(self._cache, full_path, value)
        logger.debug(f"Cache updated at path: {full_path}, with value: {value}")
