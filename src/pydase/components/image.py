from typing import Any

from pydase.data_service.data_service import DataService


class Image(DataService):
    def __init__(
        self,
        value: bytes | str = "",
    ) -> None:
        self.value = value
        super().__init__()

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "value":
            if isinstance(__value, bytes):
                __value = __value.decode()
        return super().__setattr__(__name, __value)
