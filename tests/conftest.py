import logging

import pytest


@pytest.fixture
def caplog(caplog: pytest.LogCaptureFixture):
    logger = logging.getLogger("pydase")
    logger.propagate = True

    yield caplog
