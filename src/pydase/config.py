from typing import Literal

from confz import BaseConfig, EnvSource


class OperationMode(BaseConfig):  # type: ignore[misc]
    environment: Literal["development", "production"] = "development"

    CONFIG_SOURCES = EnvSource(allow=["ENVIRONMENT"])
