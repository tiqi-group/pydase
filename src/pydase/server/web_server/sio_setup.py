import asyncio
import logging
from typing import Any, TypedDict

import click
import socketio  # type: ignore[import-untyped]

from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.utils.helpers import get_object_attr_from_path
from pydase.utils.logging import SocketIOHandler
from pydase.utils.serialization.deserializer import Deserializer
from pydase.utils.serialization.serializer import SerializedObject, dump

logger = logging.getLogger(__name__)


class UpdateDict(TypedDict):
    """
    A TypedDict subclass representing a dictionary used for updating attributes in a
    DataService.

    Attributes:
    ----------
    access_path : string
        The full access path of the attribute to be updated.
    value : SerializedObject
        The serialized new value to be assigned to the attribute.
    """

    access_path: str
    value: SerializedObject


class TriggerMethodDict(TypedDict):
    access_path: str
    args: SerializedObject
    kwargs: SerializedObject


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
        full_access_path: str, value: Any, cached_value_dict: SerializedObject
    ) -> None:
        if cached_value_dict != {}:

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


def setup_sio_events(sio: socketio.AsyncServer, state_manager: StateManager) -> None:  # noqa: C901
    @sio.event  # type: ignore
    async def connect(sid: str, environ: Any) -> None:
        logging.debug("Client [%s] connected", click.style(str(sid), fg="cyan"))

    @sio.event  # type: ignore
    async def disconnect(sid: str) -> None:
        logging.debug("Client [%s] disconnected", click.style(str(sid), fg="cyan"))

    @sio.event  # type: ignore
    async def service_serialization(sid: str) -> SerializedObject:
        logging.debug(
            "Client [%s] requested service serialization",
            click.style(str(sid), fg="cyan"),
        )
        return state_manager.cache

    @sio.event
    async def update_value(sid: str, data: UpdateDict) -> SerializedObject | None:  # type: ignore
        path = data["access_path"]

        try:
            state_manager.set_service_attribute_value_by_path(
                path=path, serialized_value=data["value"]
            )
        except Exception as e:
            logger.exception(e)
            return dump(e)

    @sio.event
    async def get_value(sid: str, access_path: str) -> SerializedObject:
        try:
            return state_manager._data_service_cache.get_value_dict_from_cache(
                access_path
            )
        except Exception as e:
            logger.exception(e)
            return dump(e)

    @sio.event
    async def trigger_method(sid: str, data: TriggerMethodDict) -> Any:
        try:
            method = get_object_attr_from_path(
                state_manager.service, data["access_path"]
            )
            args = Deserializer.deserialize(data["args"])
            kwargs: dict[str, Any] = Deserializer.deserialize(data["kwargs"])
            return dump(method(*args, **kwargs))
        except Exception as e:
            logger.error(e)
            return dump(e)


def setup_logging_handler(sio: socketio.AsyncServer) -> None:
    logger = logging.getLogger()
    logger.addHandler(SocketIOHandler(sio))
