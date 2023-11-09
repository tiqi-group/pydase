import logging
from typing import TYPE_CHECKING, Any

from pydase.utils.serializer import set_nested_value_by_path

if TYPE_CHECKING:
    from pydase import DataService

logger = logging.getLogger(__name__)


class DataServiceCache:
    def __init__(self, service: "DataService") -> None:
        self._cache: dict[str, Any] = {}
        self.service = service
        self._initialize_cache()

    @property
    def cache(self) -> dict[str, Any]:
        return self._cache

    def _initialize_cache(self) -> None:
        """Initializes the cache and sets up the callback."""
        logger.debug("Initializing cache.")
        self._cache = self.service.serialize()
        self.service._callback_manager.add_notification_callback(self.update_cache)

    def update_cache(self, parent_path: str, name: str, value: Any) -> None:
        # Remove the part before the first "." in the parent_path
        parent_path = ".".join(parent_path.split(".")[1:])

        # Construct the full path
        full_path = f"{parent_path}.{name}" if parent_path else name

        set_nested_value_by_path(self._cache, full_path, value)
