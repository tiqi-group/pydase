import logging
from typing import TYPE_CHECKING, Any, cast

from pydase.utils.serialization.serializer import (
    SerializedObject,
    get_nested_dict_by_path,
    set_nested_value_by_path,
)

if TYPE_CHECKING:
    from pydase import DataService

logger = logging.getLogger(__name__)


class DataServiceCache:
    def __init__(self, service: "DataService") -> None:
        self._cache: SerializedObject
        self.service = service
        self._initialize_cache()

    @property
    def cache(self) -> SerializedObject:
        return self._cache

    def _initialize_cache(self) -> None:
        """Initializes the cache and sets up the callback."""
        logger.debug("Initializing cache.")
        self._cache = self.service.serialize()

    def update_cache(self, full_access_path: str, value: Any) -> None:
        set_nested_value_by_path(
            cast(dict[str, SerializedObject], self._cache["value"]),
            full_access_path,
            value,
        )

    def get_value_dict_from_cache(self, full_access_path: str) -> SerializedObject:
        return get_nested_dict_by_path(
            cast(dict[str, SerializedObject], self._cache["value"]),
            full_access_path,
        )
