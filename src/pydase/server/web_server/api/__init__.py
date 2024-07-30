import logging

import aiohttp.web
import aiohttp_middlewares.error

import pydase.server.web_server.api.v1.application
from pydase.data_service.state_manager import StateManager

logger = logging.getLogger(__name__)


def create_api_application(state_manager: StateManager) -> aiohttp.web.Application:
    api_application = aiohttp.web.Application(
        middlewares=(aiohttp_middlewares.error.error_middleware(),)
    )

    api_application.add_subapp(
        "/v1/",
        pydase.server.web_server.api.v1.application.create_api_application(
            state_manager
        ),
    )

    return api_application
