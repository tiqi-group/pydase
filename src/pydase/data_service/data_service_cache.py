import logging
from typing import TYPE_CHECKING, Any, cast

from pydase.utils.serialization.serializer import (
    get_nested_dict_by_path,
    set_nested_value_by_path,
)
from pydase.utils.serialization.types import SerializedObject

if TYPE_CHECKING:
    from pydase import DataService

logger = logging.getLogger(__name__)


class DataServiceCache:
    """Maintains a serialized cache of the current state of a DataService instance.

    This class is responsible for storing and updating a representation of the service's
    public attributes and properties. It is primarily used by the StateManager and the
    web server to serve consistent state to clients without accessing the DataService
    attributes directly.

    The cache is initialized once upon construction by serializing the full state of
    the service. After that, it can be incrementally updated using attribute paths and
    values as notified by the
    [`DataServiceObserver`][pydase.data_service.data_service_observer.DataServiceObserver].

    Args:
        service: The DataService instance whose state should be cached.
    """

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
            cast("dict[str, SerializedObject]", self._cache["value"]),
            full_access_path,
            value,
        )

    def get_value_dict_from_cache(self, full_access_path: str) -> SerializedObject:
        return get_nested_dict_by_path(
            cast("dict[str, SerializedObject]", self._cache["value"]),
            full_access_path,
        )
