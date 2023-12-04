import logging
from typing import TYPE_CHECKING, Any

from pydase.utils.serializer import (
    SerializationPathError,
    SerializationValueError,
    get_nested_dict_by_path,
    set_nested_value_by_path,
)

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

    def update_cache(self, full_access_path: str, value: Any) -> None:
        set_nested_value_by_path(self._cache, full_access_path, value)

    def get_value_dict_from_cache(self, full_access_path: str) -> dict[str, Any]:
        try:
            return get_nested_dict_by_path(self._cache, full_access_path)
        except (SerializationPathError, SerializationValueError, KeyError):
            return {}
