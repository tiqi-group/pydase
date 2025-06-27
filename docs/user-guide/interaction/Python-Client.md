# Python RPC Client

The [`pydase.Client`][pydase.Client] allows you to connect to a remote `pydase` service using Socket.IO, facilitating interaction with the service as though it were running locally.

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

## Automatic Proxy Updates

By default, the client listens for attribute and structure changes from the server and dynamically updates its internal proxy representation. This ensures that value changes or newly added attributes on the server appear in the client proxy without requiring reconnection or manual refresh.

This is useful, for example, when [integrating the client into another service](#integrating-the-client-into-another-service). However, if you want to avoid this behavior (e.g., to reduce network traffic or avoid frequent re-syncing), you can disable it. When passing `auto_update_proxy=False` to the client, the proxy will not track changes after the initial connection:

```python
client = pydase.Client(
    url="ws://localhost:8001",
    auto_update_proxy=False
)
```

## Direct API Access

In addition to using the `proxy` object, users may access the server API directly via the following methods:

```python
client = pydase.Client(url="ws://localhost:8001")

# Get the current value of an attribute
value = client.get_value("device.voltage")

# Update an attribute
client.update_value("device.voltage", 5.0)

# Call a method on the remote service
result = client.trigger_method("device.reset")
```

This bypasses the proxy and is useful for lower-level access to individual service endpoints.

## Accessing Services Behind Firewalls or SSH Gateways

If your service is only reachable through a private network or SSH gateway, you can route your connection through a local SOCKS5 proxy using the `proxy_url` parameter.

See [Connecting Through a SOCKS5 Proxy](../advanced/SOCKS-Proxy.md) for details.

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
        client_id="my_pydase_client_id",  # optional, defaults to system hostname
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
- By setting `block_until_connected=False`, the service can start without waiting for the connection to succeed.
- The `client_id` is optional. If not specified, it defaults to the system hostname, which will be sent in the `X-Client-Id` HTTP header for logging or authentication on the server side.

## Custom `socketio.AsyncClient` Connection Parameters

You can configure advanced connection options by passing arguments to the underlying [`AsyncClient`][socketio.AsyncClient] via `sio_client_kwargs`. For example:

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
