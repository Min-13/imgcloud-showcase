# Lab 07: Horizontal Scaling and TLS Termination

## Learning Objectives

By the end of this lab you will be able to:

- Run multiple copies of a service side-by-side (horizontal scaling)
- Terminate TLS at the edge using nginx as a reverse proxy
- Generate a self-signed TLS certificate for development
- Observe load balancing and health-check behaviour in a running system
- Trigger per-instance unhealthiness to watch traffic shift between replicas

---

## Overview

Production deployments rarely serve traffic directly from an application process.
Instead, a **reverse proxy** sits in front of the application containers and handles:

| Concern | nginx handles it so the app doesn't have to |
|---------|---------------------------------------------|
| TLS/HTTPS | Terminates the TLS connection; proxies plain HTTP internally |
| Load balancing | Distributes requests across multiple app instances |
| Health checking | Stops routing to instances that return errors |
| HTTP→HTTPS redirect | Forces all plain-text traffic to upgrade |

In this lab you will add nginx to your Docker Compose stack, generate a
self-signed certificate, run **two** frontend containers, and observe how
traffic shifts when one instance reports itself unhealthy.

```
Browser
  │  HTTPS (your HTTPS port)
  ▼
nginx ── TLS termination
  │   │
  │   └─ HTTP (port 8080) → STUDENTNAME-frontend2
  └──── HTTP (port 8080) → STUDENTNAME-frontend1
                                  │
                         gRPC ────┤
                                  ▼
                        STUDENTNAME-imgprocessor
```

---

## Prerequisites

- A working LAB03 or LAB04 `docker-compose.yml` in your repository
- Two free ports from your range in `PORTS.md` (one for HTTPS, one for the HTTP→HTTPS redirect)
- `openssl` available on your development machine (already installed on the class server)

---

## Part 1: Generate a Self-Signed TLS Certificate

TLS requires a **certificate** (public key + identity) and a **private key**.
For production you get these from a Certificate Authority (CA) such as Let's Encrypt.
For development and learning, you can generate a *self-signed* certificate with `openssl`.

Create a `certs/` subdirectory next to your `docker-compose.yml`, then run:

```bash
mkdir -p certs

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/key.pem \
    -out    certs/cert.pem \
    -subj "/CN=localhost/O=CSC420/C=US"
```

| Flag | Meaning |
|------|---------|
| `-x509` | Output a self-signed certificate (not a CSR) |
| `-nodes` | Do **not** encrypt the private key with a passphrase (nginx needs to read it at startup) |
| `-days 365` | Certificate is valid for one year |
| `-newkey rsa:2048` | Generate a new 2048-bit RSA key pair |
| `-keyout` | Where to write the private key |
| `-out` | Where to write the certificate |
| `-subj` | Distinguished Name embedded in the certificate |

You should now have two files:

```
certs/cert.pem   ← certificate (public, safe to share)
certs/key.pem    ← private key (keep secret, never commit to git)
```

> **Important:** The **private key** must never be committed to git.  Add it to
> your `.gitignore` now.  The certificate itself (`cert.pem`) contains only
> public information and **should** be committed — it is your submission artifact
> proving TLS is configured.
>
> ```
> # .gitignore — only exclude the private key
> certs/key.pem
> ```

---

## Part 2: Write an nginx Configuration File

Create `nginx/nginx.conf` alongside your `docker-compose.yml`.  Your
configuration needs to do three things:

**Block 1 — Upstream pool**

Define a named upstream group containing both frontend instances.  Each server
entry specifies the container name and port.  Set the passive health-checking
parameters so nginx will temporarily stop routing to an instance that returns
several consecutive errors.  (What nginx directive controls the failure threshold?
What controls the cool-down window?)

**Block 2 — HTTP → HTTPS redirect**

A `server` block listening on port 80 that permanently redirects all requests to
the HTTPS equivalent URL.  The redirect should preserve the original hostname and
request path.

**Block 3 — HTTPS server**

A `server` block listening on port 443 with SSL enabled.  It needs to:

- Reference the certificate and key files you will mount from `certs/`
- Allow only TLS 1.2 and TLS 1.3
- Proxy all requests (`location /`) to the upstream pool defined in Block 1
- Set the standard forwarding headers so the application receives the real client
  IP and the original scheme

Consult the resources below to find the specific directives for each requirement:

- [nginx upstream module](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)
- [nginx proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [nginx SSL module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)

See [LAB07-NGINX.md](LAB07-NGINX.md) for guidance on what each block needs to
accomplish without the full solution.
See [LAB07-TLS.md](LAB07-TLS.md) for TLS background and why self-signed certificates trigger browser warnings.

---

## Part 3: Update docker-compose.yml

You have been updating `docker-compose.yml` since Lab03.  Apply the following
changes on your own — the descriptions below tell you *what* to change; you
should know *how* from previous labs.

**Existing frontend service**

- Rename the service and container to `STUDENTNAME-frontend1`.
- Remove the public `ports:` mapping — nginx will handle all public traffic.
- Add the `INSTANCE_ID=frontend1` environment variable to distinguish this
  instance in responses.

**Second frontend service**

- Add a second service `STUDENTNAME-frontend2` using the same image and
  configuration as `frontend1`, but with `INSTANCE_ID=frontend2`.  It does not
  need a public port mapping either.

**nginx service**

- Use the official `nginx:alpine` image.
- Expose two ports from your `PORTS.md` range: one mapped to container port 443
  (HTTPS) and one mapped to container port 80 (HTTP redirect).
- Mount your `nginx/nginx.conf` into the path nginx loads for virtual-host
  configs (`/etc/nginx/conf.d/default.conf`).
- Mount your `certs/` directory into the path referenced by your `ssl_certificate`
  and `ssl_certificate_key` directives.
- Add `depends_on` entries for both frontend services.

Make sure all three services share the same Docker network.

---

## Part 4: Start the Stack and Verify TLS

```bash
# Build and start all services
docker compose up --build -d

# Check that all containers are running
docker compose ps
```

Test the HTTPS endpoint (the `-k` flag tells curl to accept self-signed certificates):

```bash
# Basic HTTPS request
curl -k https://localhost:YOUR_HTTPS_PORT/health

# Show response headers — look for X-Instance-ID
curl -k -I https://localhost:YOUR_HTTPS_PORT/health

# Verify that plain HTTP redirects to HTTPS (follow redirects with -L)
curl -k -L http://localhost:YOUR_HTTP_PORT/health
```

You should see output similar to:

```json
{
  "instance_id": "frontend1",
  "message": "Frontend is running",
  "services": { "processor": "healthy", ... },
  "status": "healthy"
}
```

---

## Part 5: Observe Load Balancing with the Instance ID

Send several requests in a row and watch the `X-Instance-ID` header alternate between `frontend1` and `frontend2`:

```bash
for i in $(seq 1 6); do
    curl -k -sI https://localhost:YOUR_HTTPS_PORT/health | grep X-Instance-ID
done
```

You should see `frontend1` and `frontend2` alternating, confirming round-robin load balancing.

---

## Part 6: Simulate an Unhealthy Instance

The frontend now exposes a `POST /api/toggle-unhealthy` endpoint.  Calling it
flips a per-instance flag that makes **all endpoints** on that instance return
HTTP 503 (except the toggle endpoint itself, which stays reachable so you can
restore the instance).  Because each container has its own memory, toggling one
instance does not affect the other.

### Step 1 — Force frontend1 unhealthy

nginx is the only public entry point, so you need to reach the individual
container directly.  Find the internal IP or use `docker exec`:

```bash
# Option A: use docker exec to call the endpoint inside the container
docker exec STUDENTNAME-frontend1 \
    wget -qO- --method=POST http://localhost:8080/api/toggle-unhealthy

# Option B: if you temporarily add a direct port mapping for debugging:
curl -s -X POST http://localhost:DIRECT_PORT/api/toggle-unhealthy
```

Expected response:
```json
{
  "instance_id": "frontend1",
  "message": "Instance frontend1 is now unhealthy",
  "unhealthy": true
}
```

Confirm the instance is now returning 503 from its own health endpoint:

```bash
docker exec STUDENTNAME-frontend1 \
    wget -qO- http://localhost:8080/health
# → HTTP 503
```

### Step 2 — Watch traffic shift to frontend2

Because nginx uses **passive** health checking, it needs to observe a few
consecutive failures before it considers the server down.  Generate some traffic:

```bash
for i in $(seq 1 10); do
    curl -k -sI https://localhost:YOUR_HTTPS_PORT/health | grep X-Instance-ID
done
```

After the first few failures from `frontend1`, nginx will temporarily stop
routing to it and you should see only `frontend2` in the responses.

> **What you are observing:** nginx's `max_fails` counter increments each time
> the upstream returns an error (5xx).  Once the threshold is reached, nginx
> marks the server as unavailable for `fail_timeout` seconds and routes all
> traffic to the remaining healthy instances.

### Step 3 — Restore frontend1

```bash
docker exec STUDENTNAME-frontend1 \
    wget -qO- --method=POST http://localhost:8080/api/toggle-unhealthy
```

After `fail_timeout` expires, nginx will re-probe `frontend1` and resume
sending it traffic.

---

## Checklist / Submission Requirements

Your submission must include:

- [ ] `nginx/nginx.conf` — nginx reverse proxy configuration
- [ ] `certs/cert.pem` — self-signed certificate committed as a submission artifact
- [ ] `certs/key.pem` is listed in `.gitignore` (do **not** commit the private key)
- [ ] `docker-compose.yml` updated with two frontend services and the nginx service
- [ ] `docker compose up --build -d` starts all services without errors
- [ ] `curl -k https://localhost:YOUR_HTTPS_PORT/health` returns HTTP 200 with JSON
- [ ] Plain HTTP (`http://localhost:YOUR_HTTP_PORT/`) redirects to HTTPS (301)
- [ ] Multiple requests show `X-Instance-ID` alternating between `frontend1` and `frontend2`
- [ ] `POST /api/toggle-unhealthy` on one instance makes that instance return 503 on all its endpoints
- [ ] After toggling, traffic through nginx shifts to the remaining healthy instance

---

## Submission

When your stack is working end-to-end, submit as follows:

```bash
git add nginx/nginx.conf certs/cert.pem docker-compose.yml
git commit -m "Complete Lab07"
git tag lab07-final
git push origin main --tags
```

**What to include:**

- `nginx/nginx.conf` — your reverse proxy configuration
- `certs/cert.pem` — your self-signed certificate (**not** the private key)
- `docker-compose.yml` — updated with both frontend services and the nginx service

**Do not include:** `certs/key.pem` — confirm it is listed in `.gitignore` before pushing.

---

## Additional Resources

- [LAB07-TLS.md](LAB07-TLS.md) — TLS/HTTPS concepts explained
- [LAB07-NGINX.md](LAB07-NGINX.md) — nginx configuration deep dive
- [nginx upstream module documentation](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)
- [openssl req man page](https://www.openssl.org/docs/man1.1.1/man1/req.html)
