from pathlib import Path
from typing import Any, TypedDict

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from pydase import DataService
from pydase.version import __version__


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


class WebAPI:
    __sio_app: socketio.ASGIApp
    __fastapi_app: FastAPI

    def __init__(  # noqa: CFQ002
        self,
        service: DataService,
        frontend: str | Path | None = None,
        css: str | Path | None = None,
        enable_CORS: bool = True,
        info: dict[str, Any] = {},
        *args: Any,
        **kwargs: Any,
    ):
        self.service = service
        self.frontend = frontend
        self.css = css
        self.enable_CORS = enable_CORS
        self.info = info
        self.args = args
        self.kwargs = kwargs

        self.setup_socketio()
        self.setup_fastapi_app()

    def setup_socketio(self) -> None:
        # the socketio ASGI app, to notify clients when params update
        if self.enable_CORS:
            sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
        else:
            sio = socketio.AsyncServer(async_mode="asgi")

        @sio.event  # type: ignore
        def frontend_update(sid: str, data: UpdateDict) -> Any:
            logger.debug(f"Received frontend update: {data}")
            path_list, attr_name = data["parent_path"].split("."), data["name"]
            path_list.remove("DataService")  # always at the start, does not do anything
            return self.service.update_DataService_attribute(
                path_list=path_list, attr_name=attr_name, value=data["value"]
            )

        self.__sio = sio
        self.__sio_app = socketio.ASGIApp(self.__sio)

    def setup_fastapi_app(self) -> None:  # noqa: CFQ004
        app = FastAPI()

        if self.enable_CORS:
            app.add_middleware(
                CORSMiddleware,
                allow_credentials=True,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
        app.mount("/ws", self.__sio_app)

        # @app.get("/version", include_in_schema=False)
        @app.get("/version")
        def version() -> str:
            return __version__

        @app.get("/name")
        def name() -> str:
            return self.service.get_service_name()

        @app.get("/info")
        def info() -> dict[str, Any]:
            return self.info

        @app.get("/service-properties")
        def service_properties() -> dict[str, Any]:
            return self.service.serialize()

        app.mount(
            "/",
            StaticFiles(
                directory=Path(__file__).parent.parent / "frontend",
                html=True,
            ),
        )

        self.__fastapi_app = app

    def add_endpoint(self, name: str) -> None:
        # your endpoint creation code
        pass

    def get_custom_openapi(self) -> None:
        # your custom openapi generation code
        pass

    @property
    def sio(self) -> socketio.AsyncServer:
        return self.__sio

    @property
    def fastapi_app(self) -> FastAPI:
        return self.__fastapi_app
