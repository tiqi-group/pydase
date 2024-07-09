import base64
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.request import urlopen

from pydase.data_service.data_service import DataService

if TYPE_CHECKING:
    from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class Image(DataService):
    def __init__(self) -> None:
        super().__init__()
        self._value: str = ""
        self._format: str = ""

    @property
    def value(self) -> str:
        return self._value

    @property
    def format(self) -> str:
        return self._format

    def load_from_path(self, path: Path | str) -> None:
        with open(path, "rb") as image_file:
            image_data = image_file.read()
        format_ = self._get_image_format_from_bytes(image_data)
        if format_ is None:
            logger.error("Unsupported image format. Skipping...")
            return
        value_ = base64.b64encode(image_data)
        self._load_from_base64(value_, format_)

    def load_from_matplotlib_figure(self, fig: "Figure", format_: str = "png") -> None:
        buffer = io.BytesIO()
        fig.savefig(buffer, format=format_)
        value_ = base64.b64encode(buffer.getvalue())
        self._load_from_base64(value_, format_)

    def load_from_url(self, url: str) -> None:
        with urlopen(url) as response:
            image_data = response.read()
        format_ = self._get_image_format_from_bytes(image_data)
        if format_ is None:
            logger.error("Unsupported image format. Skipping...")
            return
        value_ = base64.b64encode(image_data)
        self._load_from_base64(value_, format_)

    def load_from_base64(self, value_: bytes, format_: str | None = None) -> None:
        if format_ is None:
            format_ = self._get_image_format_from_bytes(base64.b64decode(value_))
            if format_ is None:
                logger.warning(
                    "Format of passed byte string could not be determined. Skipping..."
                )
                return
        self._load_from_base64(value_, format_)

    def _load_from_base64(self, value_: bytes, format_: str) -> None:
        value = value_.decode("utf-8")
        self._value = value
        self._format = format_

    def _get_image_format_from_bytes(self, value_: bytes) -> str | None:
        format_map = {
            b"\xff\xd8": "JPEG",
            b"\x89PNG": "PNG",
            b"GIF": "GIF",
            b"RIFF": "WEBP",
        }
        for signature, format_name in format_map.items():
            if value_.startswith(signature):
                return format_name
        return None
