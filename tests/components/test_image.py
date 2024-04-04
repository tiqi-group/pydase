import logging

import pydase
import pydase.components
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.utils.serialization.serializer import dump
from pytest import LogCaptureFixture

logger = logging.getLogger(__name__)


def test_image_functions(caplog: LogCaptureFixture) -> None:
    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.my_image = pydase.components.Image()

    service_instance = MyService()
    state_manager = StateManager(service_instance)
    DataServiceObserver(state_manager)

    service_instance.my_image.load_from_url("https://cataas.com/cat")

    caplog.clear()


def test_image_serialization() -> None:
    class MyService(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.my_image = pydase.components.Image()

    assert dump(MyService()) == {
        "full_access_path": "",
        "name": "MyService",
        "type": "DataService",
        "value": {
            "my_image": {
                "full_access_path": "my_image",
                "name": "Image",
                "type": "Image",
                "value": {
                    "format": {
                        "full_access_path": "my_image.format",
                        "type": "str",
                        "value": "",
                        "readonly": True,
                        "doc": None,
                    },
                    "load_from_base64": {
                        "full_access_path": "my_image.load_from_base64",
                        "type": "method",
                        "value": None,
                        "readonly": True,
                        "doc": None,
                        "async": False,
                        "signature": {
                            "parameters": {
                                "value_": {
                                    "annotation": "<class 'bytes'>",
                                    "default": {},
                                },
                                "format_": {
                                    "annotation": "str | None",
                                    "default": {
                                        "type": "NoneType",
                                        "value": None,
                                        "readonly": False,
                                        "doc": None,
                                    },
                                },
                            },
                            "return_annotation": {},
                        },
                        "frontend_render": False,
                    },
                    "load_from_matplotlib_figure": {
                        "full_access_path": "my_image.load_from_matplotlib_figure",
                        "type": "method",
                        "value": None,
                        "readonly": True,
                        "doc": None,
                        "async": False,
                        "signature": {
                            "parameters": {
                                "fig": {"annotation": "Figure", "default": {}},
                                "format_": {
                                    "annotation": "<class 'str'>",
                                    "default": {
                                        "type": "str",
                                        "value": "png",
                                        "readonly": False,
                                        "doc": None,
                                    },
                                },
                            },
                            "return_annotation": {},
                        },
                        "frontend_render": False,
                    },
                    "load_from_path": {
                        "full_access_path": "my_image.load_from_path",
                        "type": "method",
                        "value": None,
                        "readonly": True,
                        "doc": None,
                        "async": False,
                        "signature": {
                            "parameters": {
                                "path": {
                                    "annotation": "pathlib.Path | str",
                                    "default": {},
                                }
                            },
                            "return_annotation": {},
                        },
                        "frontend_render": False,
                    },
                    "load_from_url": {
                        "full_access_path": "my_image.load_from_url",
                        "type": "method",
                        "value": None,
                        "readonly": True,
                        "doc": None,
                        "async": False,
                        "signature": {
                            "parameters": {
                                "url": {"annotation": "<class 'str'>", "default": {}}
                            },
                            "return_annotation": {},
                        },
                        "frontend_render": False,
                    },
                    "value": {
                        "full_access_path": "my_image.value",
                        "type": "str",
                        "value": "",
                        "readonly": True,
                        "doc": None,
                    },
                },
                "readonly": False,
                "doc": None,
            }
        },
        "readonly": False,
        "doc": None,
    }
