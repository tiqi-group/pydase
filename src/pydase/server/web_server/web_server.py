import asyncio
import logging
from pathlib import Path
from typing import Any

import socketio  # type: ignore[import-untyped]
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.server.web_server.sio_server import (
    setup_sio_server,
)
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
    files directory.

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
        **kwargs (Any): Additional unused keyword arguments.
    """

    def __init__(  # noqa: PLR0913
        self,
        data_service_observer: DataServiceObserver,
        host: str,
        port: int,
        css: str | Path | None = None,
        enable_cors: bool = True,
        **kwargs: Any,
    ) -> None:
        self.observer = data_service_observer
        self.state_manager = self.observer.state_manager
        self.service = self.state_manager.service
        self.port = port
        self.host = host
        self.css = css
        self.enable_cors = enable_cors
        self._loop: asyncio.AbstractEventLoop

        self._setup_fastapi_app()
        self.web_server = uvicorn.Server(
            uvicorn.Config(self.__fastapi_app, host=self.host, port=self.port)
        )
        # overwrite uvicorn's signal handlers, otherwise it will bogart SIGINT and
        # SIGTERM, which makes it impossible to escape out of
        self.web_server.install_signal_handlers = lambda: None  # type: ignore[method-assign]

    async def serve(self) -> Any:
        """Starts the server. This method should be implemented as an asynchronous
        method, which means that it should be able to run concurrently with other tasks.
        """
        self._loop = asyncio.get_running_loop()
        self._setup_socketio()
        await self.web_server.serve()

    def _setup_socketio(self) -> None:
        self._sio = setup_sio_server(self.observer, self.enable_cors, self._loop)
        self.__sio_app = socketio.ASGIApp(self._sio)

    def _setup_fastapi_app(self) -> None:
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
            return self.service.get_service_name()

        @app.get("/service-properties")
        def service_properties() -> dict[str, Any]:
            return self.state_manager.cache

        # exposing custom.css file provided by user
        if self.css is not None:

            @app.get("/custom.css")
            async def styles() -> FileResponse:
                return FileResponse(str(self.css))

        app.mount(
            "/",
            StaticFiles(
                directory=Path(__file__).parent.parent / "frontend",
                html=True,
            ),
        )

        self.__fastapi_app = app
