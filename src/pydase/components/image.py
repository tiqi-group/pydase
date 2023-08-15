import base64
import io
from pathlib import Path

import PIL.Image
from loguru import logger
from urllib.request import urlopen

from pydase.data_service.data_service import DataService


class Figure:
    """Mock class for matplotlib.Figure"""

    def savefig(self, format="png"):
        pass


class Image(DataService):
    def __init__(
        self,
    ) -> None:
        self._value: str = ""
        self._format: str = ""
        super().__init__()

    @property
    def value(self) -> str:
        return self._value

    @property
    def format(self) -> str:
        return self._format

    def load_from_path(self, path: Path | str) -> None:
        with PIL.Image.open(path) as image:
            self._load_from_PIL(image)

    def load_from_matplotlib_figure(self, fig: Figure, format_: str = "png") -> None:
        buffer = io.BytesIO()
        fig.savefig(buffer, format=format_)
        value_ = base64.b64encode(buffer.getvalue())
        self._load_from_base64(value_, format_)

    def load_from_url(self, url: str):
        image = PIL.Image.open(urlopen(url))
        self._load_from_PIL(image)

    def load_from_base64(self, value_: bytes, format_: str | None = None) -> None:
        if format_ is None:
            format_ = self._get_image_format_from_bytes(value_)
        self._load_from_base64(value_, format_)

    def _load_from_base64(self, value_: bytes, format_: str) -> None:
        value = value_.decode("utf-8") if isinstance(value_, bytes) else value_
        self._value = value
        self._format = format_

    def _load_from_PIL(self, image: PIL.Image.Image) -> None:
        if image.format is not None:
            format_ = image.format
            buffer = io.BytesIO()
            image.save(buffer, format=format_)
            value_ = base64.b64encode(buffer.getvalue())
            self._load_from_base64(value_, format_)
        else:
            logger.error("Image format is 'None'. Skipping...")

    def _get_image_format_from_bytes(self, value_: bytes):
        image_data = base64.b64decode(value_)
        # Create a writable memory buffer for the image
        image_buffer = io.BytesIO(image_data)
        # Read the image from the buffer
        image = PIL.Image.open(image_buffer)
        return image.format
