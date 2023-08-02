from pathlib import Path
from typing import Literal

from confz import ConfZ, ConfZEnvSource

CONFIG_DIR = Path(__file__).parent.parent.parent.resolve() / "config"


class OperationMode(ConfZ):  # type: ignore
    environment: Literal["development"] | Literal["production"] = "production"

    CONFIG_SOURCES = ConfZEnvSource(allow=["ENVIRONMENT"])
