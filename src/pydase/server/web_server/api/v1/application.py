import logging
from typing import TYPE_CHECKING

import aiohttp.web
import aiohttp_middlewares.error
import click

from pydase.data_service.state_manager import StateManager
from pydase.server.web_server.api.v1.endpoints import (
    get_value,
    trigger_method,
    update_value,
)
from pydase.utils.serialization.serializer import dump

if TYPE_CHECKING:
    from pydase.server.web_server.sio_setup import TriggerMethodDict, UpdateDict

logger = logging.getLogger(__name__)

STATUS_OK = 200
STATUS_FAILED = 400


def get_log_id(request: aiohttp.web.Request) -> str:
    client_id_header = request.headers.get("x-client-id", None)
    remote_username_header = request.headers.get("remote-user", None)

    if client_id_header is not None:
        log_id = f"id={click.style(client_id_header, fg='cyan')}"
    elif remote_username_header is not None:
        log_id = f"user={click.style(remote_username_header, fg='cyan')}"
    else:
        log_id = f"id={click.style(None, fg='cyan')}"

    return log_id


def create_api_application(state_manager: StateManager) -> aiohttp.web.Application:
    api_application = aiohttp.web.Application(
        middlewares=(aiohttp_middlewares.error.error_middleware(),)
    )

    async def _get_value(request: aiohttp.web.Request) -> aiohttp.web.Response:
        log_id = get_log_id(request)

        access_path = request.rel_url.query["access_path"]

        logger.info("Client [%s] is getting the value of '%s'", log_id, access_path)

        status = STATUS_OK
        try:
            result = get_value(state_manager, access_path)
        except Exception as e:
            logger.exception(e)
            result = dump(e)
            status = STATUS_FAILED
        return aiohttp.web.json_response(result, status=status)

    async def _update_value(request: aiohttp.web.Request) -> aiohttp.web.Response:
        log_id = get_log_id(request)

        data: UpdateDict = await request.json()

        logger.info(
            "Client [%s] is updating the value of '%s'", log_id, data["access_path"]
        )

        try:
            update_value(state_manager, data)

            return aiohttp.web.json_response()
        except Exception as e:
            logger.exception(e)
            return aiohttp.web.json_response(dump(e), status=STATUS_FAILED)

    async def _trigger_method(request: aiohttp.web.Request) -> aiohttp.web.Response:
        log_id = get_log_id(request)

        access_path = request.rel_url.query["access_path"]

        logger.info("Client [%s] is triggering the method '%s'", log_id, access_path)

        data: TriggerMethodDict = await request.json()

        try:
            return aiohttp.web.json_response(trigger_method(state_manager, data))

        except Exception as e:
            logger.exception(e)
            return aiohttp.web.json_response(dump(e), status=STATUS_FAILED)

    api_application.router.add_get("/get_value", _get_value)
    api_application.router.add_put("/update_value", _update_value)
    api_application.router.add_put("/trigger_method", _trigger_method)

    return api_application
