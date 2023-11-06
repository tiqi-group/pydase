import logging

import pydase
from pydase.data_service.data_service_cache import DataServiceCache
from pydase.utils.helpers import get_nested_value_from_DataService_by_path_and_key

logger = logging.getLogger()


def test_nested_attributes_cache_callback() -> None:
    class SubClass(pydase.DataService):
        name = "Hello"

    class ServiceClass(pydase.DataService):
        class_attr = SubClass()
        name = "World"

    test_service = ServiceClass()
    cache = DataServiceCache(test_service)

    test_service.name = "Peepz"
    assert (
        get_nested_value_from_DataService_by_path_and_key(cache.cache, "name")
        == "Peepz"
    )

    test_service.class_attr.name = "Ciao"
    assert (
        get_nested_value_from_DataService_by_path_and_key(
            cache.cache, "class_attr.name"
        )
        == "Ciao"
    )
