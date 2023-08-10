import base64
import io
from pathlib import Path

import PIL.Image
from loguru import logger

from pydase.data_service.data_service import DataService


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
            self._load_from_PIL_Image(image)

    def load_from_base64(self, value: bytes) -> None:
        if isinstance(value, bytes):
            # Decode the base64 string
            image_data = base64.b64decode(value)

            # Create a writable memory buffer for the image
            image_buffer = io.BytesIO(image_data)

            # Read the image from the buffer
            image = PIL.Image.open(image_buffer)
            self._load_from_PIL_Image(image)

    def _load_from_PIL_Image(self, image: PIL.Image.Image) -> None:
        if isinstance(image, PIL.Image.Image):
            if image.format is not None:
                self._format = image.format
                buffered = io.BytesIO()
                image.save(buffered, format=self._format)
                img_base64 = base64.b64encode(buffered.getvalue())

                self._value = img_base64.decode()
            else:
                logger.error("Image format is 'None'. Skipping...")
