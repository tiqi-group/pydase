from typing import Literal, Union

from confz import BaseConfig, EnvSource


class OperationMode(BaseConfig):  # type: ignore
    environment: Union[Literal["development"], Literal["production"]] = "development"

    CONFIG_SOURCES = EnvSource(allow=["ENVIRONMENT"])
