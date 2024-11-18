# Deploying Services Behind a Reverse Proxy

In some environments, you may need to deploy your services behind a reverse proxy. Typically, this involves adding a CNAME record for your service that points to the reverse proxy in your DNS server. The proxy then routes requests to the `pydase` backend on the appropriate web server port.

However, in scenarios where you don’t control the DNS server, or where adding new CNAME records is time-consuming, `pydase` supports **service multiplexing** using a path prefix. This means multiple services can be hosted on a single CNAME (e.g., `services.example.com`), with each service accessible through a unique path such as `services.example.com/my-service`.

To ensure seamless operation, the reverse proxy must strip the path prefix (e.g., `/my-service`) from the request URL and forward it as the `X-Forwarded-Prefix` header. `pydase` then uses this header to dynamically adjust the frontend paths, ensuring all resources are correctly located.

## Example Deployment with Traefik

Below is an example setup using [Traefik](https://doc.traefik.io/traefik/), a widely-used reverse proxy. This configuration demonstrates how to forward requests for a `pydase` service using a path prefix.

### 1. Reverse Proxy Configuration

Save the following configuration to a file (e.g., `/etc/traefik/dynamic_conf/my-service-config.yml`):

```yaml
http:
  routers:
    my-service-route:
      rule: PathPrefix(`/my-service`)
      entryPoints:
        - web
      service: my-service
      middlewares:
        - strip-prefix
  services:
    my-service:
      loadBalancer:
        servers:
          - url: http://127.0.0.1:8001
  middlewares:
    strip-prefix:
      stripprefix:
        prefixes: /my-service
```

This configuration:

- Routes requests with the path prefix `/my-service` to the `pydase` backend.
- Strips the prefix (`/my-service`) from the request URL using the `stripprefix` middleware.
- Forwards the stripped prefix as the `X-Forwarded-Prefix` header.

### 2. Static Configuration for Traefik

Ensure Traefik is set up to use the dynamic configuration. Add this to your Traefik static configuration (e.g., `/etc/traefik/traefik.yml`):

```yaml
providers:
  file:
    filename: /etc/traefik/dynamic_conf/my-service-config.yml
entrypoints:
  web:
    address: ":80"
```

### 3. Accessing the Service

Once configured, your `pydase` service will be accessible at `http://services.example.com/my-service`. The path prefix will be handled transparently by `pydase`, so you don’t need to make any changes to your application code or frontend resources.
