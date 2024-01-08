import json
import logging
import tempfile
from pathlib import Path

import pydase
from pydase.data_service.data_service_observer import DataServiceObserver
from pydase.data_service.state_manager import StateManager
from pydase.server.web_server.web_server import WebServer

logger = logging.getLogger(__name__)


def test_web_settings() -> None:
    class SubClass(pydase.DataService):
        name = "Hello"

    class ServiceClass(pydase.DataService):
        def __init__(self) -> None:
            super().__init__()
            self.attr_1 = SubClass()
            self.added = "added"

    service_instance = ServiceClass()
    state_manager = StateManager(service_instance)
    observer = DataServiceObserver(state_manager)
    with tempfile.TemporaryDirectory() as tmp:
        web_settings = {
            "attr_1": {"displayName": "Attribute"},
            "attr_1.name": {"displayName": "Attribute name"},
        }
        web_settings_file = Path(tmp) / "web_settings.json"

        with web_settings_file.open("w") as file:
            file.write(json.dumps(web_settings))

        server = WebServer(
            observer,
            host="0.0.0.0",
            port=8001,
            generate_new_web_settings=True,
            config_dir=Path(tmp),
        )
        new_web_settings = server.web_settings

        # existing entries are not overwritten, new entries are appended
        assert new_web_settings == {**web_settings, "added": {"displayName": "added"}}
