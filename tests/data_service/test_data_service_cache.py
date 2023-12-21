import logging

import pydase
import pytest
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager

logger = logging.getLogger()


def test_nested_attributes_cache_callback() -> None:
    class SubClass(pydase.DataService):
        name = "Hello"

    class ServiceClass(pydase.DataService):
        class_attr = SubClass()
        name = "World"

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.name = "Peepz"
    assert (
        state_manager._data_service_cache.get_value_dict_from_cache("name")["value"]
        == "Peepz"
    )

    service_instance.class_attr.name = "Ciao"
    assert (
        state_manager._data_service_cache.get_value_dict_from_cache("class_attr.name")[
            "value"
        ]
        == "Ciao"
    )


@pytest.mark.asyncio
async def test_task_status_update() -> None:
    class ServiceClass(pydase.DataService):
        name = "World"

        async def my_method(self) -> None:
            pass

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    assert (
        state_manager._data_service_cache.get_value_dict_from_cache("my_method")["type"]
        == "method"
    )
    assert (
        state_manager._data_service_cache.get_value_dict_from_cache("my_method")[
            "value"
        ]
        is None
    )

    service_instance.start_my_method()  # type: ignore
    assert (
        state_manager._data_service_cache.get_value_dict_from_cache("my_method")["type"]
        == "method"
    )
    assert (
        state_manager._data_service_cache.get_value_dict_from_cache("my_method")[
            "value"
        ]
        == {}
    )
