from pathlib import Path
from typing import Literal

from confz import BaseConfig, EnvSource


class OperationMode(BaseConfig):  # type: ignore[misc]
    environment: Literal["testing", "development", "production"] = "development"
    """The service's operation mode."""

    CONFIG_SOURCES = EnvSource(allow=["ENVIRONMENT"])


class ServiceConfig(BaseConfig):  # type: ignore[misc]
    """Service configuration.

    Variables can be set through environment variables prefixed with `SERVICE_` or an
    `.env` file containing those variables.
    """

    config_dir: Path = Path("config")
    """Configuration directory"""
    web_port: int = 8001
    """Web server port"""

    CONFIG_SOURCES = EnvSource(allow_all=True, prefix="SERVICE_", file=".env")


class WebServerConfig(BaseConfig):  # type: ignore[misc]
    """The service's web server configuration."""

    generate_web_settings: bool = False
    """Should generate web_settings.json file"""

    CONFIG_SOURCES = EnvSource(allow=["GENERATE_WEB_SETTINGS"])
