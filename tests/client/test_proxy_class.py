import asyncio
from unittest.mock import AsyncMock, call, patch

import pytest

from pydase import components
from pydase.client.proxy_class import ProxyClass


@pytest.mark.asyncio
async def test_serialize_fallback_inside_event_loop() -> None:
    loop = asyncio.get_running_loop()
    mock_sio = AsyncMock()
    proxy = ProxyClass(sio_client=mock_sio, loop=loop, reconnect=lambda: None)

    with patch.object(
        components.DeviceConnection, "serialize", return_value={"value": {}}
    ) as mock_fallback:
        result = proxy.serialize()

    mock_fallback.assert_has_calls(calls=[call(), call()])
    assert isinstance(result, dict)
