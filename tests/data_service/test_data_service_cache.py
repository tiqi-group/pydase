import logging

import pydase
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
        state_manager.cache_manager.get_value_dict_from_cache("name")["value"]
        == "Peepz"
    )

    service_instance.class_attr.name = "Ciao"
    assert (
        state_manager.cache_manager.get_value_dict_from_cache("class_attr.name")[
            "value"
        ]
        == "Ciao"
    )
