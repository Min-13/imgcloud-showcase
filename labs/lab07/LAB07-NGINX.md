# Lab 07 — nginx as a Reverse Proxy

> **Terminology note:** In this document *upstream service* or *application instance*
> refers to the Python/Flask containers (which the rest of the course calls
> "frontend" services).  nginx uses the term *upstream* for any server it proxies
> requests to, regardless of where that server sits in your application stack.

---

## Role of nginx in This Architecture

nginx sits between the internet and your application containers.  It:

1. **Terminates TLS** — decrypts HTTPS requests and forwards plain HTTP internally.
2. **Load balances** — distributes requests across the upstream pool.
3. **Redirects HTTP → HTTPS** — upgrades any plain-text connection automatically.
4. **Sets proxy headers** — tells upstream services the real client IP and the
   original protocol.

---

## Configuration File Structure

nginx reads configuration from `/etc/nginx/nginx.conf`.  When you mount a file
at `/etc/nginx/conf.d/default.conf`, the main config `include`s it automatically
(this is how the official `nginx:alpine` Docker image works).

Your configuration for this lab needs three top-level blocks:

```nginx
upstream <pool_name> { ... }   # 1. Define the upstream pool

server {                        # 2. HTTP server (redirect only)
    listen 80;
    ...
}

server {                        # 3. HTTPS server (TLS termination + proxy)
    listen 443 ssl;
    ...
}
```

Consult the [nginx upstream module docs](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)
and the [ngx_http_proxy_module docs](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
for the specific directives you will need.

---

## The `upstream` Block

The `upstream` block names a pool of servers and controls how nginx distributes
traffic.  Key directives:

| Directive | Meaning |
|-----------|---------|
| `server <host>:<port>` | An application instance in the pool |
| `max_fails=N` | Mark the instance temporarily unavailable after N consecutive failures |
| `fail_timeout=Ns` | The window for counting failures, and the cool-down period before retrying |

By default nginx uses **round-robin** load balancing — each request goes to the
next server in the list in turn.

**Passive vs. active health checking:** The nginx open-source version uses *passive*
health checking — it only marks an instance unavailable after observing actual
failures on real proxied requests.  It does not actively poll `/health`.
This is why you need to send a few requests through the proxy before nginx
detects that an instance has gone unhealthy.

---

## The HTTP Redirect Block

The second `server` block listens on port 80 and issues a permanent redirect to
HTTPS.  Key directives:

| Directive | Meaning |
|-----------|---------|
| `listen 80` | Accept plain-HTTP connections |
| `server_name _` | Match any hostname (wildcard catch-all) |
| `return 301 <url>` | Issue a permanent redirect; use nginx variables to preserve the hostname and path |

---

## The HTTPS Server Block

The third `server` block listens on port 443 with SSL enabled.

### SSL directives

| Directive | Meaning |
|-----------|---------|
| `ssl_certificate` | Path to the PEM-encoded certificate |
| `ssl_certificate_key` | Path to the PEM-encoded private key |
| `ssl_protocols` | Allowed TLS protocol versions (use TLSv1.2 and TLSv1.3) |
| `ssl_ciphers` | Allowed cipher suites |

### `location /` — proxy directives

| Directive | Meaning |
|-----------|---------|
| `proxy_pass http://<upstream_name>` | Forward the request to the named upstream pool |
| `proxy_set_header Host $host` | Preserve the original `Host` header |
| `proxy_set_header X-Real-IP $remote_addr` | Pass the client's IP to the application |
| `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for` | Append client IP to the forwarding chain |
| `proxy_set_header X-Forwarded-Proto $scheme` | Tell the application whether the original request was HTTP or HTTPS |
| `proxy_connect_timeout` | How long to wait when opening a connection to an upstream instance |
| `proxy_read_timeout` | How long to wait for an upstream instance to send a response |

---

## Volume Mounts in Docker Compose

Two volume mounts are needed for the nginx service:

1. Mount your `nginx/nginx.conf` to `/etc/nginx/conf.d/default.conf` — the
   `nginx:alpine` image automatically includes all files under `/etc/nginx/conf.d/`.
2. Mount your `certs/` directory to `/etc/nginx/certs` — this is the path to
   reference in your `ssl_certificate` and `ssl_certificate_key` directives
   (e.g. `/etc/nginx/certs/cert.pem` and `/etc/nginx/certs/key.pem`).

Use the `:ro` (read-only) mount option — nginx only needs to *read* these files,
and read-only mounts are a good security practice.

---

## Useful nginx Commands Inside the Container

```bash
# Validate the configuration without restarting
docker exec STUDENTNAME-nginx nginx -t

# Reload configuration without dropping connections (after editing nginx.conf)
docker exec STUDENTNAME-nginx nginx -s reload

# View nginx access logs in real time
docker logs -f STUDENTNAME-nginx
```

---

## Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `nginx: [emerg] cannot load certificate` | Wrong path to cert.pem | Verify the volume mount path matches `ssl_certificate` |
| `502 Bad Gateway` | Application instances not running | Run `docker compose ps` and check both frontend containers |
| `curl: (35) SSL connect error` | TLS negotiation failed | Check `ssl_protocols` matches your curl/openssl version |
| All requests go to one instance | Only one instance is healthy | Check `docker compose ps` — is the other container running? |
| nginx returns 301 instead of proxying | Request sent to port 80 | Use the HTTPS port in your curl command |
