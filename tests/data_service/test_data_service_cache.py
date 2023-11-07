import logging

import pydase
from pydase.data_service.data_service_cache import DataServiceCache
from pydase.utils.serializer import get_nested_dict_by_path

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
    assert get_nested_dict_by_path(cache.cache, "name")["value"] == "Peepz"

    test_service.class_attr.name = "Ciao"
    assert get_nested_dict_by_path(cache.cache, "class_attr.name")["value"] == "Ciao"
