import logging
from typing import Any

import aiohttp.web
import aiohttp_middlewares.error

from pydase.data_service.state_manager import StateManager
from pydase.server.web_server.sio_setup import TriggerMethodDict, UpdateDict
from pydase.utils.helpers import get_object_attr_from_path
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.serializer import dump
from pydase.utils.serialization.types import SerializedObject

logger = logging.getLogger(__name__)

API_VERSION = "v1"


def update_value(state_manager: StateManager, data: UpdateDict) -> None:
    path = data["access_path"]

    state_manager.set_service_attribute_value_by_path(
        path=path, serialized_value=data["value"]
    )


def get_value(state_manager: StateManager, access_path: str) -> SerializedObject:
    return state_manager._data_service_cache.get_value_dict_from_cache(access_path)


def trigger_method(state_manager: StateManager, data: TriggerMethodDict) -> Any:
    method = get_object_attr_from_path(state_manager.service, data["access_path"])

    serialized_args = data.get("args", None)
    args = loads(serialized_args) if serialized_args else []

    serialized_kwargs = data.get("kwargs", None)
    kwargs: dict[str, Any] = loads(serialized_kwargs) if serialized_kwargs else {}

    return dump(method(*args, **kwargs))


def create_api_application(state_manager: StateManager) -> aiohttp.web.Application:
    api_application = aiohttp.web.Application(
        middlewares=(aiohttp_middlewares.error.error_middleware(),)
    )

    async def _get_value(request: aiohttp.web.Request) -> aiohttp.web.Response:
        logger.info("Handle api request: %s", request)
        api_version = request.match_info["version"]
        logger.info("Version number: %s", api_version)

        access_path = request.rel_url.query["access_path"]

        try:
            result = get_value(state_manager, access_path)
        except Exception as e:
            logger.exception(e)
            result = dump(e)
        return aiohttp.web.json_response(result)

    async def _update_value(request: aiohttp.web.Request) -> aiohttp.web.Response:
        data: UpdateDict = await request.json()

        try:
            update_value(state_manager, data)

            return aiohttp.web.Response()
        except Exception as e:
            logger.exception(e)
            return aiohttp.web.json_response(dump(e))

    async def _trigger_method(request: aiohttp.web.Request) -> aiohttp.web.Response:
        data: TriggerMethodDict = await request.json()

        try:
            trigger_method(state_manager, data)

            return aiohttp.web.Response()
        except Exception as e:
            logger.exception(e)
            return aiohttp.web.json_response(dump(e))

    api_application.router.add_get("/{version}/get_value", _get_value)
    api_application.router.add_post("/{version}/update_value", _update_value)
    api_application.router.add_post("/{version}/trigger_method", _trigger_method)

    return api_application
