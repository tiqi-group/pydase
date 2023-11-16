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


def test_task_status_update() -> None:
    class ServiceClass(pydase.DataService):
        name = "World"

        async def my_method(self) -> None:
            pass

    test_service = ServiceClass()
    cache = DataServiceCache(test_service)
    assert get_nested_dict_by_path(cache.cache, "my_method")["type"] == "method"
    assert get_nested_dict_by_path(cache.cache, "my_method")["value"] is None

    test_service.start_my_method()  # type: ignore
    assert get_nested_dict_by_path(cache.cache, "my_method")["type"] == "method"
    assert get_nested_dict_by_path(cache.cache, "my_method")["value"] == {}
