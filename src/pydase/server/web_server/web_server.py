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
from pydase.server.web_server.sio_server_wrapper import SioServerWrapper
from pydase.version import __version__

logger = logging.getLogger(__name__)


class WebServer:
    """
    A Protocol that defines the interface for additional servers.

    This protocol sets the standard for how additional servers should be implemented
    to ensure compatibility with the main Server class. The protocol requires that
    any server implementing it should have an __init__ method for initialization and a
    serve method for starting the server.

    Parameters:
    -----------
    service: DataService
        The instance of DataService that the server will use. This could be the main
        application or a specific service that the server will provide.

    port: int
        The port number at which the server will be accessible. This should be a valid
        port number, typically in the range 1024-65535.

    host: str
        The hostname or IP address at which the server will be hosted. This could be a
        local address (like '127.0.0.1' for localhost) or a public IP address.

    state_manager: StateManager
        The state manager managing the state cache and persistence of the exposed
        service.

    **kwargs: Any
        Any additional parameters required for initializing the server. These parameters
        are specific to the server's implementation.
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
        self.__sio = SioServerWrapper(self.observer, self.enable_cors, self._loop).sio
        self.__sio_app = socketio.ASGIApp(self.__sio)

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
