import asyncio
import logging
from typing import Any, TypedDict

import socketio  # type: ignore[import-untyped]

from pydase.data_service.data_service import process_callable_attribute
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.utils.helpers import get_object_attr_from_path_list
from pydase.utils.logging import SocketIOHandler
from pydase.utils.serializer import dump

logger = logging.getLogger(__name__)


class UpdateDict(TypedDict):
    """
    A TypedDict subclass representing a dictionary used for updating attributes in a
    DataService.

    Attributes:
    ----------
    name : str
        The name of the attribute to be updated in the DataService instance.
        If the attribute is part of a nested structure, this would be the name of the
        attribute in the last nested object. For example, for an attribute access path
        'attr1.list_attr[0].attr2', 'attr2' would be the name.

    parent_path : str
        The access path for the parent object of the attribute to be updated. This is
        used to construct the full access path for the attribute. For example, for an
        attribute access path 'attr1.list_attr[0].attr2', 'attr1.list_attr[0]' would be
        the parent_path.

    value : Any
        The new value to be assigned to the attribute. The type of this value should
        match the type of the attribute to be updated.
    """

    name: str
    parent_path: str
    value: Any


class RunMethodDict(TypedDict):
    """
    A TypedDict subclass representing a dictionary used for running methods from the
    exposed DataService.

    Attributes:
        name (str): The name of the method to be run.
        parent_path (str): The access path for the parent object of the method to be
            run. This is used to construct the full access path for the method. For
            example, for an method with access path 'attr1.list_attr[0].method_name',
            'attr1.list_attr[0]' would be the parent_path.
        kwargs (dict[str, Any]): The arguments passed to the method.
    """

    name: str
    parent_path: str
    kwargs: dict[str, Any]


class UpdateWebSettingsDict(TypedDict):
    """
    A TypedDict subclass representing a dictionary used for updating attributes in a
    DataService.

    Attributes:
    ----------
    access_path : str
        The access path for the component object. This does not have to be an attribute
        but can also
        For example, for an
        attribute access path 'attr1.list_attr[0].attr2', 'attr1.list_attr[0]' would be
        the parent_path.

    config_option : str
        The web setting to be changed, e.g. 'display_name' or 'precision' for
        NumberComponents.

    value : Any
        The new value to be assigned to the attribute. The type of this value should
        match the type of the attribute to be updated.
    """

    access_path: str
    config_option: str
    value: Any


def setup_sio_server(
    observer: DataServiceObserver,
    enable_cors: bool,
    loop: asyncio.AbstractEventLoop,
) -> socketio.AsyncServer:
    """
    Sets up and configures a Socket.IO asynchronous server.

    Args:
        observer (DataServiceObserver):
          The observer managing state updates and communication.
        enable_cors (bool):
          Flag indicating whether CORS should be enabled for the server.
        loop (asyncio.AbstractEventLoop):
          The event loop in which the server will run.

    Returns:
        socketio.AsyncServer: The configured Socket.IO asynchronous server.
    """

    state_manager = observer.state_manager

    if enable_cors:
        sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
    else:
        sio = socketio.AsyncServer(async_mode="asgi")

    setup_sio_events(sio, state_manager)
    setup_logging_handler(sio)

    # Add notification callback to observer
    def sio_callback(
        full_access_path: str, value: Any, cached_value_dict: dict[str, Any]
    ) -> None:
        if cached_value_dict != {}:
            serialized_value = dump(value)
            if cached_value_dict["type"] != "method":
                cached_value_dict["type"] = serialized_value["type"]

            cached_value_dict["value"] = serialized_value["value"]

            async def notify() -> None:
                try:
                    await sio.emit(
                        "notify",
                        {
                            "data": {
                                "full_access_path": full_access_path,
                                "value": cached_value_dict,
                            }
                        },
                    )
                except Exception as e:
                    logger.warning("Failed to send notification: %s", e)

            loop.create_task(notify())

    observer.add_notification_callback(sio_callback)

    return sio


def setup_sio_events(sio: socketio.AsyncServer, state_manager: StateManager) -> None:
    @sio.event
    def set_attribute(sid: str, data: UpdateDict) -> Any:
        logger.debug("Received frontend update: %s", data)
        path_list = [*data["parent_path"].split("."), data["name"]]
        path_list.remove("DataService")  # always at the start, does not do anything
        path = ".".join(path_list)
        return state_manager.set_service_attribute_value_by_path(
            path=path, value=data["value"]
        )

    @sio.event
    def run_method(sid: str, data: RunMethodDict) -> Any:
        logger.debug("Running method: %s", data)
        path_list = [*data["parent_path"].split("."), data["name"]]
        path_list.remove("DataService")  # always at the start, does not do anything
        method = get_object_attr_from_path_list(state_manager.service, path_list)
        return process_callable_attribute(method, data["kwargs"])

    @sio.event
    def web_settings(sid: str, data: UpdateWebSettingsDict) -> Any:
        logger.debug("Received web settings update: %s", data)
        path_list, config_option, value = (
            data["access_path"].split("."),
            data["config_option"],
            data["value"],
        )
        path_list.pop(0)  # remove first entry (specifies root object, not needed)


def setup_logging_handler(sio: socketio.AsyncServer) -> None:
    logger = logging.getLogger()
    logger.addHandler(SocketIOHandler(sio))