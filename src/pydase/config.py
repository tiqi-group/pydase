from pathlib import Path
from typing import Literal

from confz import BaseConfig, EnvSource


class OperationMode(BaseConfig):  # type: ignore[misc]
    environment: Literal["development", "production"] = "development"

    CONFIG_SOURCES = EnvSource(allow=["ENVIRONMENT"])


class ServiceConfig(BaseConfig):  # type: ignore[misc]
    config_dir: Path = Path("config")
    web_port: int = 8001
    rpc_port: int = 18871

    CONFIG_SOURCES = EnvSource(allow_all=True, prefix="SERVICE_")


class WebServerConfig(BaseConfig):  # type: ignore[misc]
    generate_web_settings: bool = False

    CONFIG_SOURCES = EnvSource(allow=["GENERATE_WEB_SETTINGS"])
