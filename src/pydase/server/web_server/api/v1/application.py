import inspect
import logging
from functools import partial
from typing import TYPE_CHECKING

import aiohttp.web
import aiohttp_middlewares.error

from pydase.data_service.state_manager import StateManager
from pydase.server.web_server.api.v1.endpoints import (
    get_value,
    trigger_async_method,
    trigger_method,
    update_value,
)
from pydase.utils.helpers import get_object_attr_from_path
from pydase.utils.serialization.serializer import dump

if TYPE_CHECKING:
    from pydase.server.web_server.sio_setup import TriggerMethodDict, UpdateDict

logger = logging.getLogger(__name__)

STATUS_OK = 200
STATUS_FAILED = 400


async def _get_value(
    request: aiohttp.web.Request, state_manager: StateManager
) -> aiohttp.web.Response:
    logger.info("Handle api request: %s", request)

    access_path = request.rel_url.query["access_path"]

    status = STATUS_OK
    try:
        result = get_value(state_manager, access_path)
    except Exception as e:
        logger.exception(e)
        result = dump(e)
        status = STATUS_FAILED
    return aiohttp.web.json_response(result, status=status)


async def _update_value(
    request: aiohttp.web.Request, state_manager: StateManager
) -> aiohttp.web.Response:
    data: UpdateDict = await request.json()

    try:
        update_value(state_manager, data)

        return aiohttp.web.json_response()
    except Exception as e:
        logger.exception(e)
        return aiohttp.web.json_response(dump(e), status=STATUS_FAILED)


async def _trigger_method(
    request: aiohttp.web.Request, state_manager: StateManager
) -> aiohttp.web.Response:
    data: TriggerMethodDict = await request.json()

    method = get_object_attr_from_path(state_manager.service, data["access_path"])

    try:
        if inspect.iscoroutinefunction(method):
            method_return = await trigger_async_method(
                state_manager=state_manager, data=data
            )
        else:
            method_return = trigger_method(state_manager=state_manager, data=data)

        return aiohttp.web.json_response(method_return)

    except Exception as e:
        logger.exception(e)
        return aiohttp.web.json_response(dump(e), status=STATUS_FAILED)


def create_api_application(state_manager: StateManager) -> aiohttp.web.Application:
    api_application = aiohttp.web.Application(
        middlewares=(aiohttp_middlewares.error.error_middleware(),)
    )

    api_application.router.add_get(
        "/get_value", partial(_get_value, state_manager=state_manager)
    )
    api_application.router.add_put(
        "/update_value", partial(_update_value, state_manager=state_manager)
    )
    api_application.router.add_put(
        "/trigger_method", partial(_trigger_method, state_manager=state_manager)
    )

    return api_application
