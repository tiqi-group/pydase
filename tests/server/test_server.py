import signal

from pytest_mock import MockerFixture

import pydase


def test_signal_handling(mocker: MockerFixture):
    # Mock os._exit and signal.signal
    mock_exit = mocker.patch("os._exit")
    mock_signal = mocker.patch("signal.signal")

    class MyService(pydase.DataService):
        pass

    # Instantiate your server object
    server = pydase.Server(MyService())

    # Call the method to install signal handlers
    server.install_signal_handlers()

    # Check if the signal handlers were registered correctly
    assert mock_signal.call_args_list == [
        mocker.call(signal.SIGINT, server.handle_exit),
        mocker.call(signal.SIGTERM, server.handle_exit),
    ]

    # Simulate receiving a SIGINT signal for the first time
    server.handle_exit(signal.SIGINT, None)
    assert server.should_exit  # assuming should_exit is public
    mock_exit.assert_not_called()

    # Simulate receiving a SIGINT signal for the second time
    server.handle_exit(signal.SIGINT, None)
    mock_exit.assert_called_once_with(1)
