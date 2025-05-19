# Python RPC Client

The [`pydase.Client`][pydase.Client] allows you to connect to a remote `pydase` service using socket.io, facilitating interaction with the service as though it were running locally.

## Basic Usage

```python
import pydase

# Replace <ip_addr> and <service_port> with the appropriate values for your service
client_proxy = pydase.Client(url="ws://<ip_addr>:<service_port>").proxy
# For SSL-encrypted services, use the wss protocol
# client_proxy = pydase.Client(url="wss://your-domain.ch").proxy

# Interact with the service attributes as if they were local
client_proxy.voltage = 5.0
print(client_proxy.voltage)  # Expected output: 5.0
```

This example shows how to set and retrieve the `voltage` attribute through the client proxy.
The proxy acts as a local representation of the remote service, enabling intuitive interaction.

The proxy class automatically synchronizes with the server's attributes and methods, keeping itself up-to-date with any changes. This dynamic synchronization essentially mirrors the server's API, making it feel like you're working with a local object.

## Context Manager Support

You can also use the client within a context manager, which automatically handles connection management (i.e., opening and closing the connection):

```python
import pydase


with pydase.Client(url="ws://localhost:8001") as client:
    client.proxy.my_method()
```

Using the context manager ensures that connections are cleanly closed once the block of code finishes executing.

## Tab Completion Support

In interactive environments like Python interpreters or Jupyter notebooks, the proxy supports tab completion. This allows users to explore available methods and attributes.

## Integrating the Client into Another Service

You can integrate a `pydase` client proxy within another service. Here's an example of how to set this up:

```python
import pydase

class MyService(pydase.DataService):
    proxy = pydase.Client(
        url="ws://<ip_addr>:<service_port>",
        block_until_connected=False,
        client_id="my_pydase_client_id",
    ).proxy
    # For SSL-encrypted services, use the wss protocol
    # proxy = pydase.Client(
    #     url="wss://your-domain.ch",
    #     block_until_connected=False,
    #     client_id="my_pydase_client_id",
    # ).proxy

if __name__ == "__main__":
    service = MyService()
    # Create a server that exposes this service
    server = pydase.Server(service, web_port=8002).run()
```

In this example:
- The `MyService` class has a `proxy` attribute that connects to a `pydase` service at `<ip_addr>:<service_port>`.
- By setting `block_until_connected=False`, the service can start without waiting for the connection to succeed, which is particularly useful in distributed systems where services may initialize in any order.
- By setting `client_id`, the server will provide more accurate logs of the connecting client. If set, this ID is sent as `X-Client-Id` header in the HTTP(s) request.

## Custom `socketio.AsyncClient` Connection Parameters

You can also configure advanced connection options by passing additional arguments to the underlying [`AsyncClient`][socketio.AsyncClient] via `sio_client_kwargs`. This allows you to fine-tune reconnection behaviour, delays, and other settings:

```python
client = pydase.Client(
    url="ws://localhost:8001",
    sio_client_kwargs={
        "reconnection_attempts": 3,
        "reconnection_delay": 2,
        "reconnection_delay_max": 10,
    }
).proxy
```

In this setup, the client will attempt to reconnect three times, with an initial delay of 2 seconds (each successive attempt doubles this delay) and a maximum delay of 10 seconds between attempts.
