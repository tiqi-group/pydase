import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import socketio  # type: ignore[import-untyped]
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydase.config import ServiceConfig, WebServerConfig
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.server.web_server.sio_setup import (
    setup_sio_server,
)
from pydase.utils.serializer import generate_serialized_data_paths
from pydase.version import __version__

logger = logging.getLogger(__name__)


class WebServer:
    """
    Represents a web server that adheres to the AdditionalServerProtocol, designed to
    work with a DataService instance. This server facilitates client-server
    communication and state management through web protocols and socket connections.

    The WebServer class initializes and manages a web server environment using FastAPI
    and Socket.IO, allowing for HTTP and WebSocket communications. It incorporates CORS
    (Cross-Origin Resource Sharing) support, custom CSS, and serves a frontend static
    files directory. It also initializes web server settings based on configuration
    files or generates default settings if necessary.

    Configuration for the web server (like service configuration directory and whether
    to generate new web settings) is determined in the following order of precedence:
    1. Values provided directly to the constructor.
    2. Environment variable settings (via configuration classes like
      `pydase.config.ServiceConfig` and `pydase.config.WebServerConfig`).
    3. Default values defined in the configuration classes.

    Args:
        data_service_observer (DataServiceObserver): Observer for the DataService,
          handling state updates and communication to connected clients.
        host (str): Hostname or IP address where the server is accessible. Commonly
          '0.0.0.0' to bind to all network interfaces.
        port (int): Port number on which the server listens. Typically in the range
          1024-65535 (non-standard ports).
        css (str | Path | None, optional): Path to a custom CSS file for styling the
          frontend. If None, no custom styles are applied. Defaults to None.
        enable_cors (bool, optional): Flag to enable or disable CORS policy. When True,
          CORS is enabled, allowing cross-origin requests. Defaults to True.
        config_dir (Path | None, optional): Path to the configuration
          directory where the web settings will be stored. Defaults to
          `pydase.config.ServiceConfig().config_dir`.
        generate_new_web_settings (bool | None, optional): Flag to enable or disable
          generation of new web settings if the configuration file is missing. Defaults
          to `pydase.config.WebServerConfig().generate_new_web_settings`.
        **kwargs (Any): Additional unused keyword arguments.
    """

    def __init__(  # noqa: PLR0913
        self,
        data_service_observer: DataServiceObserver,
        host: str,
        port: int,
        css: str | Path | None = None,
        enable_cors: bool = True,
        config_dir: Path = ServiceConfig().config_dir,
        generate_web_settings: bool = WebServerConfig().generate_web_settings,
        **kwargs: Any,
    ) -> None:
        self.observer = data_service_observer
        self.state_manager = self.observer.state_manager
        self.service = self.state_manager.service
        self.port = port
        self.host = host
        self.css = css
        self.enable_cors = enable_cors
        self._service_config_dir = config_dir
        self._generate_web_settings = generate_web_settings
        self._loop: asyncio.AbstractEventLoop
        self._initialise_configuration()

    async def serve(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._setup_socketio()
        self._setup_fastapi_app()
        self.web_server = uvicorn.Server(
            uvicorn.Config(self.__fastapi_app, host=self.host, port=self.port)
        )
        # overwrite uvicorn's signal handlers, otherwise it will bogart SIGINT and
        # SIGTERM, which makes it impossible to escape out of
        self.web_server.install_signal_handlers = lambda: None  # type: ignore[method-assign]
        await self.web_server.serve()

    def _initialise_configuration(self) -> None:
        logger.debug("Initialising web server configuration...")

        file_path = self._service_config_dir / "web_settings.json"

        if self._generate_web_settings:
            # File does not exist, create it with default content
            logger.debug("Generating web settings file...")
            file_path.parent.mkdir(
                parents=True, exist_ok=True
            )  # Ensure directory exists
            file_path.write_text(json.dumps(self.web_settings, indent=4))

    def _get_web_settings_from_file(self) -> dict[str, dict[str, Any]]:
        file_path = self._service_config_dir / "web_settings.json"
        web_settings = {}

        # File exists, read its content
        if file_path.exists():
            logger.debug(
                "Reading configuration from file '%s' ...", file_path.absolute()
            )

            web_settings = json.loads(file_path.read_text())

        return web_settings

    @property
    def web_settings(self) -> dict[str, dict[str, Any]]:
        current_web_settings = self._get_web_settings_from_file()
        for path in generate_serialized_data_paths(self.state_manager.cache["value"]):
            if path in current_web_settings:
                continue

            current_web_settings[path] = {"displayName": path.split(".")[-1]}

        return current_web_settings

    def _setup_socketio(self) -> None:
        self._sio = setup_sio_server(self.observer, self.enable_cors, self._loop)
        self.__sio_app = socketio.ASGIApp(self._sio)

    def _setup_fastapi_app(self) -> None:  # noqa: C901
        app = FastAPI()

        if self.enable_cors:
            app.add_middleware(
                CORSMiddleware,
                allow_credentials=True,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
        app.mount("/ws", self.__sio_app)

        @app.get("/version")
        def version() -> str:
            return __version__

        @app.get("/name")
        def name() -> str:
            return type(self.service).__name__

        @app.get("/service-properties")
        def service_properties() -> dict[str, Any]:
            return self.state_manager.cache

        @app.get("/web-settings")
        def web_settings() -> dict[str, Any]:
            return self.web_settings

        # exposing custom.css file provided by user
        if self.css is not None:

            @app.get("/custom.css")
            async def styles() -> FileResponse:
                return FileResponse(str(self.css))

        app.mount(
            "/",
            StaticFiles(
                directory=Path(__file__).parent.parent.parent / "frontend",
                html=True,
            ),
        )

        self.__fastapi_app = app
