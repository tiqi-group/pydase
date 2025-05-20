# Connecting Through a SOCKS5 Proxy

If your target service is only reachable via an SSH gateway or resides behind a 
firewall, you can route your [`pydase.Client`][pydase.Client] connection through a local
SOCKS5 proxy. This is particularly useful in network environments where direct access to
the service is not possible.

## Setting Up a SOCKS5 Proxy

You can create a local [SOCKS5 proxy](https://en.wikipedia.org/wiki/SOCKS) using SSH's
`-D` option:

```bash
ssh -D 2222 user@gateway.example.com
```

This command sets up a SOCKS5 proxy on `localhost:2222`, securely forwarding traffic
over the SSH connection.

## Using the Proxy in Your Python Client

Once the proxy is running, configure the [`pydase.Client`][pydase.Client] to route 
traffic through it using the `proxy_url` parameter:

```python
import pydase

client = pydase.Client(
    url="ws://target-service:8001",
    proxy_url="socks5://localhost:2222"
).proxy
```

* You can also use this setup with `wss://` URLs for encrypted WebSocket connections.

## Installing Required Dependencies

To use this feature, you must install the optional `socks` dependency group, which 
includes [`aiohttp_socks`](https://pypi.org/project/aiohttp-socks/):

- `poetry`
  ```bash
  poetry add "pydase[socks]"
  ```
- `pip`
  ```bash
  pip install "pydase[socks]"
  ```
