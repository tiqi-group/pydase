from enum import Enum
from pathlib import Path
from typing import Any, TypedDict, get_type_hints

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from pyDataInterface import DataService
from pyDataInterface.config import OperationMode
from pyDataInterface.version import __version__


class FrontendUpdate(TypedDict):
    name: str
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

    def setup_socketio(self) -> None:  # noqa: C901
        # the socketio ASGI app, to notify clients when params update
        if self.enable_CORS:
            sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
        else:
            sio = socketio.AsyncServer(async_mode="asgi")

        @sio.event  # type: ignore
        def frontend_update(sid: str, data: FrontendUpdate) -> Any:
            logger.debug(f"Received frontend update: {data}")
            attr = getattr(self.service, data["name"])
            if isinstance(attr, DataService):
                attr.apply_updates(data["value"])
            elif isinstance(attr, Enum):
                setattr(
                    self.service, data["name"], attr.__class__[data["value"]["value"]]
                )
            elif callable(attr):
                args: dict[str, Any] = data["value"]["args"]
                type_hints = get_type_hints(attr)

                # Convert arguments to their hinted types
                for arg_name, arg_value in args.items():
                    if arg_name in type_hints:
                        arg_type = type_hints[arg_name]
                        if isinstance(arg_type, type):
                            # Attempt to convert the argument to its hinted type
                            try:
                                args[arg_name] = arg_type(arg_value)
                            except ValueError:
                                msg = f"Failed to convert argument '{arg_name}' to type {arg_type.__name__}"
                                logger.error(msg)
                                return msg

                return attr(**args)
            else:
                setattr(self.service, data["name"], data["value"])

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

        if OperationMode().environment == "production":
            app.mount(
                "/",
                StaticFiles(
                    directory=Path(__file__).parent.parent.parent.parent
                    / "frontend"
                    / "build",
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
