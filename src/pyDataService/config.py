from typing import Literal

from confz import ConfZ, ConfZEnvSource


class OperationMode(ConfZ):  # type: ignore
    environment: Literal["development"] | Literal["production"] = "production"

    CONFIG_SOURCES = ConfZEnvSource(allow=["ENVIRONMENT"])
