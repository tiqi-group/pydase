from typing import Literal

from confz import BaseConfig, EnvSource


class OperationMode(BaseConfig):  # type: ignore
    environment: Literal["development"] | Literal["production"] = "development"

    CONFIG_SOURCES = EnvSource(allow=["ENVIRONMENT"])
