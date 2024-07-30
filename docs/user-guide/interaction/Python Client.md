# Python Client

You can connect to the service using the `pydase.Client`. Below is an example of how to establish a connection to a service and interact with it:

```python
import pydase

# Replace the hostname and port with the IP address and the port of the machine 
# where the service is running, respectively
client_proxy = pydase.Client(hostname="<ip_addr>", port=8001).proxy

# Interact with the service attributes as if they were local
client_proxy.voltage = 5.0
print(client_proxy.voltage)  # Expected output: 5.0
```

This example demonstrates setting and retrieving the `voltage` attribute through the client proxy.
The proxy acts as a local representative of the remote service, enabling straightforward interaction.

The proxy class dynamically synchronizes with the server's exposed attributes. This synchronization allows the proxy to be automatically updated with any attributes or methods that the server exposes, essentially mirroring the server's API. This dynamic updating enables users to interact with the remote service as if they were working with a local object.

## Tab Completion Support

In interactive environments such as Python interpreters and Jupyter notebooks, the proxy class supports tab completion, which allows users to explore available methods and attributes.

## Integration within Other Services

You can also integrate a client proxy within another service. Here's how you can set it up:

```python
import pydase

class MyService(pydase.DataService):
    # Initialize the client without blocking the constructor
    proxy = pydase.Client(hostname="<ip_addr>", port=8001, block_until_connected=False).proxy

if __name__ == "__main__":
    service = MyService()
    # Create a server that exposes this service; adjust the web_port as needed
    server = pydase.Server(service, web_port=8002). run()
```

In this setup, the `MyService` class has a `proxy` attribute that connects to a `pydase` service located at `<ip_addr>:8001`.
The `block_until_connected=False` argument allows the service to start up even if the initial connection attempt fails.
This configuration is particularly useful in distributed systems where services may start in any order.
