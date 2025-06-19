import asyncio
import inspect
import logging
import sys
from typing import Any, TypedDict

from pydase.utils.helpers import get_object_attr_from_path

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired

import click
import socketio  # type: ignore[import-untyped]

import pydase.utils.serialization.deserializer
import pydase.utils.serialization.serializer
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.server.web_server.api.v1 import endpoints
from pydase.utils.logging import SocketIOHandler
from pydase.utils.serialization.types import SerializedObject

logger = logging.getLogger(__name__)

# These functions can be monkey-patched by other libraries at runtime
dump = pydase.utils.serialization.serializer.dump
sio_client_manager = None


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
    args: NotRequired[SerializedObject]
    kwargs: NotRequired[SerializedObject]


class RunMethodDict(TypedDict):
    """
    A TypedDict subclass representing a dictionary used for running methods from the
    exposed DataService.

    Attributes:
        name:
            The name of the method to be run.
        parent_path:
            The access path for the parent object of the method to be run. This is used
            to construct the full access path for the method. For example, for an method
            with access path 'attr1.list_attr[0].method_name', 'attr1.list_attr[0]'
            would be the parent_path.
        kwargs:
            The arguments passed to the method.
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
        observer:
            The observer managing state updates and communication.
        enable_cors:
            Flag indicating whether CORS should be enabled for the server.
        loop:
            The event loop in which the server will run.

    Returns:
        The configured Socket.IO asynchronous server.
    """

    state_manager = observer.state_manager

    if enable_cors:
        sio = socketio.AsyncServer(
            async_mode="aiohttp",
            cors_allowed_origins="*",
            client_manager=sio_client_manager,
        )
    else:
        sio = socketio.AsyncServer(
            async_mode="aiohttp",
            client_manager=sio_client_manager,
        )

    setup_sio_events(sio, state_manager)
    setup_logging_handler(sio)

    # Add notification callback to observer
    def sio_callback(
        full_access_path: str, value: Any, cached_value_dict: SerializedObject
    ) -> None:
        if cached_value_dict != {} and loop.is_running():

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
        client_id_header = environ.get("HTTP_X_CLIENT_ID", None)
        remote_username_header = environ.get("HTTP_REMOTE_USER", None)

        if remote_username_header is not None:
            log_id = f"user={click.style(remote_username_header, fg='cyan')}"
        elif client_id_header is not None:
            log_id = f"id={click.style(client_id_header, fg='cyan')}"
        else:
            log_id = f"sid={click.style(sid, fg='cyan')}"

        async with sio.session(sid) as session:
            session["client_id"] = log_id
            logger.info("Client [%s] connected", session["client_id"])

    @sio.event  # type: ignore
    async def disconnect(sid: str) -> None:
        async with sio.session(sid) as session:
            logger.info("Client [%s] disconnected", session["client_id"])

    @sio.event  # type: ignore
    async def service_serialization(sid: str) -> SerializedObject:
        async with sio.session(sid) as session:
            logger.info(
                "Client [%s] requested service serialization", session["client_id"]
            )
        return state_manager.cache_manager.cache

    @sio.event
    async def update_value(sid: str, data: UpdateDict) -> SerializedObject | None:
        async with sio.session(sid) as session:
            logger.info(
                "Client [%s] is updating the value of '%s'",
                session["client_id"],
                data["access_path"],
            )
        try:
            endpoints.update_value(state_manager=state_manager, data=data)
        except Exception as e:
            logger.exception(e)
            return dump(e)
        return None

    @sio.event
    async def get_value(sid: str, access_path: str) -> SerializedObject:
        async with sio.session(sid) as session:
            logger.info(
                "Client [%s] is getting the value of '%s'",
                session["client_id"],
                access_path,
            )
        try:
            return endpoints.get_value(
                state_manager=state_manager, access_path=access_path
            )
        except Exception as e:
            logger.exception(e)
            return dump(e)

    @sio.event
    async def trigger_method(sid: str, data: TriggerMethodDict) -> Any:
        async with sio.session(sid) as session:
            logger.info(
                "Client [%s] is triggering the method '%s'",
                session["client_id"],
                data["access_path"],
            )
        try:
            method = get_object_attr_from_path(
                state_manager.service, data["access_path"]
            )
            if inspect.iscoroutinefunction(method):
                return await endpoints.trigger_async_method(
                    state_manager=state_manager, data=data
                )
            return endpoints.trigger_method(state_manager=state_manager, data=data)
        except Exception as e:
            logger.exception(e)
            return dump(e)


def setup_logging_handler(sio: socketio.AsyncServer) -> None:
    logging.getLogger().addHandler(SocketIOHandler(sio))
    logging.getLogger("pydase").addHandler(SocketIOHandler(sio))
