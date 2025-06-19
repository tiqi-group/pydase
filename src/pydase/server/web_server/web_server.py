import asyncio
import html
import json
import logging
from pathlib import Path
from typing import Any

import aiohttp.web
import aiohttp_middlewares.cors
import anyio

from pydase.config import ServiceConfig, WebServerConfig
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.server.web_server.api import create_api_application
from pydase.server.web_server.sio_setup import (
    setup_sio_server,
)
from pydase.utils.helpers import (
    get_path_from_path_parts,
    parse_full_access_path,
)
from pydase.utils.serialization.serializer import generate_serialized_data_paths

logger = logging.getLogger(__name__)


class WebServer:
    """
    Represents a web server that adheres to the
    [`AdditionalServerProtocol`][pydase.server.server.AdditionalServerProtocol],
    designed to work with a [`DataService`][pydase.DataService] instance. This server
    facilitates client-server communication and state management through web protocols
    and socket connections.

    The WebServer class initializes and manages a web server environment aiohttp and
    Socket.IO, allowing for HTTP and Socket.IO communications. It incorporates CORS
    (Cross-Origin Resource Sharing) support, custom CSS, and serves a static files
    directory. It also initializes web server settings based on configuration files or
    generates default settings if necessary.

    Configuration for the web server (like service configuration directory and whether
    to generate new web settings) is determined in the following order of precedence:

    1. Values provided directly to the constructor.
    2. Environment variable settings (via configuration classes like
      [`ServiceConfig`][pydase.config.ServiceConfig] and
      [`WebServerConfig`][pydase.config.WebServerConfig]).
    3. Default values defined in the configuration classes.

    Args:
        data_service_observer:
            Observer for the [`DataService`][pydase.DataService], handling state updates
            and communication to connected clients.
        host:
            Hostname or IP address where the server is accessible. Commonly '0.0.0.0'
            to bind to all network interfaces.
        port:
            Port number on which the server listens. Typically in the range 1024-65535
            (non-standard ports).
        css:
            Path to a custom CSS file for styling the frontend. If None, no custom
            styles are applied. Defaults to None.
        favicon_path:
            Path to a custom favicon.ico file. Defaults to None.
        enable_cors:
            Flag to enable or disable CORS policy. When True, CORS is enabled, allowing
            cross-origin requests. Defaults to True.
        config_dir:
            Path to the configuration directory where the web settings will be stored.
            Defaults to
            [`ServiceConfig().config_dir`][pydase.config.ServiceConfig.config_dir].
        generate_web_settings:
            Flag to enable or disable generation of new web settings if the
            configuration file is missing. Defaults to
            [`WebServerConfig().generate_web_settings`][pydase.config.WebServerConfig.generate_web_settings].
    """

    def __init__(  # noqa: PLR0913
        self,
        data_service_observer: DataServiceObserver,
        host: str,
        port: int,
        *,
        enable_frontend: bool = True,
        css: str | Path | None = None,
        favicon_path: str | Path | None = None,
        enable_cors: bool = True,
        config_dir: Path = ServiceConfig().config_dir,
        generate_web_settings: bool = WebServerConfig().generate_web_settings,
        frontend_src: Path = Path(__file__).parent.parent.parent / "frontend",
    ) -> None:
        self.observer = data_service_observer
        self.state_manager = self.observer.state_manager
        self.service = self.state_manager.service
        self.port = port
        self.host = host
        self.css = css
        self.enable_cors = enable_cors
        self.frontend_src = frontend_src
        self.favicon_path: Path | str = favicon_path  # type: ignore
        self.enable_frontend = enable_frontend

        if self.favicon_path is None:
            self.favicon_path = self.frontend_src / "favicon.ico"

        self._service_config_dir = config_dir
        self._generate_web_settings = generate_web_settings
        self._loop = asyncio.get_event_loop()
        self._sio = setup_sio_server(self.observer, self.enable_cors, self._loop)
        self._initialise_configuration()

    async def serve(self) -> None:
        async def index(
            request: aiohttp.web.Request,
        ) -> aiohttp.web.Response | aiohttp.web.FileResponse:
            forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
            escaped_proto = html.escape(forwarded_proto)

            # Read the index.html file
            index_file_path = self.frontend_src / "index.html"

            async with await anyio.open_file(index_file_path) as f:
                html_content = await f.read()

            # Inject the escaped forwarded protocol into the HTML
            modified_html = html_content.replace(
                'window.__FORWARDED_PROTO__ = "";',
                f'window.__FORWARDED_PROTO__ = "{escaped_proto}";',
            )

            # Read the X-Forwarded-Prefix header from the request
            forwarded_prefix = request.headers.get("X-Forwarded-Prefix", "")

            if forwarded_prefix != "":
                # Escape the forwarded prefix to prevent XSS
                escaped_prefix = html.escape(forwarded_prefix)

                # Inject the escaped forwarded prefix into the HTML
                modified_html = modified_html.replace(
                    'window.__FORWARDED_PREFIX__ = "";',
                    f'window.__FORWARDED_PREFIX__ = "{escaped_prefix}";',
                )
                modified_html = modified_html.replace(
                    "/assets/",
                    f"{escaped_prefix}/assets/",
                )

                modified_html = modified_html.replace(
                    "/favicon.ico",
                    f"{escaped_prefix}/favicon.ico",
                )

            return aiohttp.web.Response(text=modified_html, content_type="text/html")

        app = aiohttp.web.Application()

        # Add CORS middleware if enabled
        if self.enable_cors:
            app.middlewares.append(
                aiohttp_middlewares.cors.cors_middleware(allow_all=True)
            )

        # Define routes
        self._sio.attach(app, socketio_path="/ws/socket.io")
        if self.enable_frontend:
            app.router.add_static("/assets", self.frontend_src / "assets")
            app.router.add_get("/favicon.ico", self._favicon_route)
            app.router.add_get("/service-properties", self._service_properties_route)
            app.router.add_get("/web-settings", self._web_settings_route)
            app.router.add_get("/custom.css", self._styles_route)
        app.add_subapp("/api/", create_api_application(self.state_manager))

        if self.enable_frontend:
            app.router.add_get(r"/", index)
            app.router.add_get(r"/{tail:.*}", index)

        await aiohttp.web._run_app(
            app,
            host=self.host,
            port=self.port,
            handle_signals=False,
            print=logger.info,
            shutdown_timeout=0.1,
        )

    async def _favicon_route(
        self,
        request: aiohttp.web.Request,
    ) -> aiohttp.web.FileResponse:
        return aiohttp.web.FileResponse(self.favicon_path)

    async def _service_properties_route(
        self,
        request: aiohttp.web.Request,
    ) -> aiohttp.web.Response:
        return aiohttp.web.json_response(self.state_manager.cache_manager.cache)

    async def _web_settings_route(
        self,
        request: aiohttp.web.Request,
    ) -> aiohttp.web.Response:
        return aiohttp.web.json_response(self.web_settings)

    async def _styles_route(
        self,
        request: aiohttp.web.Request,
    ) -> aiohttp.web.FileResponse | aiohttp.web.Response:
        if self.css is not None:
            return aiohttp.web.FileResponse(self.css)

        return aiohttp.web.Response(content_type="text/css")

    def _initialise_configuration(self) -> None:
        logger.debug("Initialising web server configuration...")

        if self._generate_web_settings:
            logger.debug("Generating web settings file...")
            file_path = self._service_config_dir / "web_settings.json"

            # File does not exist, create it with default content
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
        for path in generate_serialized_data_paths(self.state_manager.cache_value):
            if path in current_web_settings:
                continue

            # Creating the display name by reversely looping through the path parts
            # until an item does not start with a square bracket, and putting the parts
            # back together again. This allows for display names like
            #       >>> 'dict_attr["some.dotted.key"]'
            display_name_parts: list[str] = []
            for item in parse_full_access_path(path)[::-1]:
                display_name_parts.insert(0, item)
                if not item.startswith("["):
                    break

            current_web_settings[path] = {
                "displayName": get_path_from_path_parts(display_name_parts),
                "display": True,
            }

        return current_web_settings
