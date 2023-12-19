from pathlib import Path
from typing import Literal

from confz import BaseConfig, EnvSource


class OperationMode(BaseConfig):  # type: ignore[misc]
    environment: Literal["development", "production"] = "development"

    CONFIG_SOURCES = EnvSource(allow=["ENVIRONMENT"])


class ServiceConfig(BaseConfig):  # type: ignore[misc]
    service_config_dir: Path = Path("config")

    CONFIG_SOURCES = EnvSource(allow=["SERVICE_CONFIG_DIR"])


class WebServerConfig(BaseConfig):  # type: ignore[misc]
    generate_new_web_settings: bool = False

    CONFIG_SOURCES = EnvSource(allow=["GENERATE_NEW_WEB_SETTINGS"])
