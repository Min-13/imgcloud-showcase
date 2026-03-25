# Dockerfile Cheatsheet

A comprehensive reference for Dockerfile instructions and syntax.

## Table of Contents
- [Basic Structure](#basic-structure)
- [Core Instructions](#core-instructions)
- [File Operations](#file-operations)
- [Execution Instructions](#execution-instructions)
- [Metadata Instructions](#metadata-instructions)
- [Multi-Stage Builds](#multi-stage-builds)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Basic Structure

A Dockerfile is a text file that contains instructions for building a Docker image. Each instruction creates a new layer in the image.

```dockerfile
# Comment
INSTRUCTION arguments
```

**Important:** Instructions are processed sequentially from top to bottom.

---

## Core Instructions

### FROM

Sets the base image for subsequent instructions. Must be the first instruction (except for ARG before FROM).

```dockerfile
# Use an official base image
FROM ubuntu:22.04

# Use a specific version
FROM python:3.11-slim

# Use a minimal base image
FROM alpine:latest

# Multi-stage build with naming
FROM golang:1.21-alpine AS builder
```

**Best Practice:** Always use specific tags instead of `latest` for reproducibility.

---

### RUN

Executes commands in a new layer on top of the current image and commits the results.

```dockerfile
# Single command
RUN apt-get update

# Multiple commands with &&
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*

# Shell form (runs in /bin/sh -c)
RUN echo "Hello World"

# Exec form (does not invoke a shell)
RUN ["executable", "param1", "param2"]
```

**Best Practice:** Combine related commands with `&&` to reduce layers. Clean up in the same layer to reduce image size.

---

### WORKDIR

Sets the working directory for subsequent instructions (RUN, CMD, ENTRYPOINT, COPY, ADD).

```dockerfile
# Set working directory
WORKDIR /app

# Create directory if it doesn't exist
WORKDIR /path/to/directory

# Use absolute paths
WORKDIR /home/user/app

# Relative paths are relative to previous WORKDIR
WORKDIR /app
WORKDIR src  # Results in /app/src
```

**Best Practice:** Use WORKDIR instead of `RUN cd /path` for clarity and reliability.

---

### ENV

Sets environment variables that persist in the built image and running containers.

```dockerfile
# Single variable
ENV NODE_ENV production

# Multiple variables (old syntax)
ENV PORT=8080 HOST=0.0.0.0

# Multiple variables (preferred syntax)
ENV PORT=8080 \
    HOST=0.0.0.0 \
    DEBUG=false

# Use in subsequent instructions
ENV APP_HOME /app
WORKDIR $APP_HOME
```

**Note:** Environment variables set with ENV persist when a container runs from the image.

---

### ARG

Defines build-time variables that users can pass at build-time with `docker build --build-arg`.

```dockerfile
# Define argument with default value
ARG VERSION=1.0.0

# Use in instructions
ARG BASE_IMAGE=python:3.11
FROM $BASE_IMAGE

# Without default value (must be provided at build time)
ARG BUILD_DATE

# Scope: ARG before FROM is outside build stages
ARG BASE_VERSION=3.11
FROM python:${BASE_VERSION}
ARG BASE_VERSION  # Re-declare to use inside build stage
RUN echo "Python version: $BASE_VERSION"
```

**Usage:** `docker build --build-arg VERSION=2.0.0 -t myapp .`

---

## File Operations

### COPY

Copies files or directories from the build context to the container filesystem.

```dockerfile
# Copy single file
COPY app.py /app/

# Copy multiple files
COPY app.py requirements.txt /app/

# Copy directory contents
COPY src/ /app/src/

# Copy with wildcard
COPY *.py /app/

# Copy and rename
COPY config.json /app/config.production.json

# Set ownership (requires --chown flag)
COPY --chown=user:group files* /app/

# Copy from a specific build stage (multi-stage builds)
COPY --from=builder /app/dist /app/
```

**Best Practice:** Use COPY instead of ADD unless you need ADD's special features (tar extraction, URL support).

---

### ADD

Similar to COPY but with additional features (auto-extraction of tar files, URL support).

```dockerfile
# Copy files (same as COPY)
ADD app.py /app/

# Auto-extract tar files
ADD archive.tar.gz /app/

# Download from URL (not recommended - use RUN wget instead)
ADD https://example.com/file.txt /app/

# Set ownership
ADD --chown=user:group files* /app/
```

**Best Practice:** Prefer COPY for simple file copying. Use ADD only when you need auto-extraction or URL downloads.

---

## Execution Instructions

### CMD

Provides defaults for executing a container. Only the last CMD in a Dockerfile takes effect.

```dockerfile
# Exec form (preferred) - does not invoke a shell
CMD ["executable", "param1", "param2"]

# Example: Run a Python app
CMD ["python", "app.py"]

# Example: Run a Node.js app
CMD ["node", "server.js"]

# Shell form - runs in /bin/sh -c
CMD command param1 param2

# Example: Shell form
CMD python app.py

# Provide default parameters to ENTRYPOINT
CMD ["--port", "8080"]
```

**Note:** CMD can be overridden when running the container: `docker run myimage custom-command`

---

### ENTRYPOINT

Configures a container to run as an executable. Difficult to override (requires --entrypoint flag).

```dockerfile
# Exec form (preferred)
ENTRYPOINT ["executable", "param1"]

# Example: Python application
ENTRYPOINT ["python", "app.py"]

# Example: Shell script
ENTRYPOINT ["/entrypoint.sh"]

# Shell form
ENTRYPOINT command param1

# Combine with CMD for default arguments
ENTRYPOINT ["python", "app.py"]
CMD ["--port", "8080"]
# Runs: python app.py --port 8080
# Override CMD: docker run myimage --port 9090
```

**Best Practice:** Use ENTRYPOINT for the main executable and CMD for default arguments.

---

### SHELL

Overrides the default shell used for the shell form of commands.

```dockerfile
# Default shell on Linux: ["/bin/sh", "-c"]
# Default shell on Windows: ["cmd", "/S", "/C"]

# Use bash instead of sh
SHELL ["/bin/bash", "-c"]

# Windows example
SHELL ["powershell", "-command"]

# Effect on subsequent RUN, CMD, ENTRYPOINT (shell form)
SHELL ["/bin/bash", "-c"]
RUN echo "This runs in bash"
```

---

## Metadata Instructions

### LABEL

Adds metadata to an image as key-value pairs.

```dockerfile
# Single label
LABEL version="1.0"

# Multiple labels
LABEL maintainer="student@example.com" \
      description="Image processing service" \
      version="1.0.0"

# Standard labels (recommended)
LABEL org.opencontainers.image.title="ImgCloud"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Your Name"
```

**View labels:** `docker inspect myimage`

---

### EXPOSE

Documents which ports the container listens on at runtime. Does not actually publish the port.

```dockerfile
# Single port
EXPOSE 8080

# Multiple ports
EXPOSE 8080 443

# Specify protocol (default is TCP)
EXPOSE 8080/tcp
EXPOSE 53/udp

# Port range
EXPOSE 8000-8010
```

**Note:** To publish ports, use `-p` flag: `docker run -p 8080:8080 myimage`

---

### VOLUME

Creates a mount point and marks it as holding externally mounted volumes.

```dockerfile
# Single volume
VOLUME /data

# Multiple volumes
VOLUME ["/var/log", "/var/db"]

# Named volume (in docker-compose or run command)
VOLUME /app/data
```

**Note:** Volumes are managed by Docker and persist after container deletion.

---

### USER

Sets the user (and optionally group) to use for RUN, CMD, and ENTRYPOINT instructions.

```dockerfile
# Switch to non-root user (best practice for security)
USER appuser

# User and group
USER appuser:appgroup

# Using UID:GID
USER 1000:1000

# Create user first, then switch
RUN useradd -m -u 1000 appuser
USER appuser
```

**Security Best Practice:** Always run as non-root user in production containers.

---

### HEALTHCHECK

Tells Docker how to test if the container is still working.

```dockerfile
# Basic health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

# Python health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Disable health check from base image
HEALTHCHECK NONE

# Options:
# --interval=DURATION (default: 30s)
# --timeout=DURATION (default: 30s)
# --start-period=DURATION (default: 0s)
# --retries=N (default: 3)
```

**Exit codes:** 0 = healthy, 1 = unhealthy

---

### STOPSIGNAL

Sets the system call signal to stop the container.

```dockerfile
# Default is SIGTERM
STOPSIGNAL SIGTERM

# Use SIGKILL
STOPSIGNAL SIGKILL

# Using signal number
STOPSIGNAL 9
```

---

## Multi-Stage Builds

Use multiple FROM instructions to create smaller final images by copying only what you need.

```dockerfile
# Stage 1: Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o myapp

# Stage 2: Runtime stage
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/myapp .
CMD ["./myapp"]
```

**Benefits:** Smaller images, better security (no build tools in final image), faster deployments.

### Copy from Named Stages

```dockerfile
FROM node:18 AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM python:3.11 AS backend
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# Copy frontend build artifacts
COPY --from=frontend-builder /app/dist ./static

CMD ["python", "app.py"]
```

---

## Best Practices

### 1. Order Matters (Caching)

Place less frequently changing instructions first to leverage Docker's layer caching.

```dockerfile
# ✅ Good - dependencies change less often than code
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]

# ❌ Bad - invalidates cache on every code change
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

### 2. Minimize Layers

Combine related commands to reduce image layers.

```dockerfile
# ✅ Good - single layer
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*

# ❌ Bad - multiple layers
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2
RUN rm -rf /var/lib/apt/lists/*
```

### 3. Use .dockerignore

Create a `.dockerignore` file to exclude unnecessary files from the build context.

```
# .dockerignore
.git
node_modules
*.log
.env
README.md
```

### 4. Use Specific Tags

```dockerfile
# ✅ Good - specific version
FROM python:3.11.5-slim

# ❌ Bad - unpredictable
FROM python:latest
```

### 5. Security

```dockerfile
# Create and use non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Don't store secrets in images
# Use build arguments or runtime environment variables
```

---

## Examples

### Python Flask Application

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Run application
CMD ["python", "app.py"]
```

### Go Application (Multi-Stage)

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server .

# Runtime stage
FROM alpine:latest
RUN apk --no-cache add ca-certificates
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
WORKDIR /home/appuser
COPY --from=builder /app/server .
RUN chown appuser:appuser server
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1
CMD ["./server"]
```

### Node.js Application

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application
COPY . .

# Create non-root user
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

CMD ["node", "server.js"]
```

---

## Quick Reference Card

| Instruction | Purpose | Example |
|-------------|---------|---------|
| `FROM` | Set base image | `FROM ubuntu:22.04` |
| `RUN` | Execute commands | `RUN apt-get update` |
| `COPY` | Copy files to image | `COPY app.py /app/` |
| `ADD` | Copy + extract/download | `ADD archive.tar.gz /app/` |
| `WORKDIR` | Set working directory | `WORKDIR /app` |
| `ENV` | Set environment variable | `ENV PORT=8080` |
| `ARG` | Build-time variable | `ARG VERSION=1.0` |
| `CMD` | Default command | `CMD ["python", "app.py"]` |
| `ENTRYPOINT` | Main executable | `ENTRYPOINT ["python"]` |
| `EXPOSE` | Document port | `EXPOSE 8080` |
| `VOLUME` | Mount point | `VOLUME /data` |
| `USER` | Set user | `USER appuser` |
| `HEALTHCHECK` | Health check | `HEALTHCHECK CMD curl ...` |
| `LABEL` | Add metadata | `LABEL version="1.0"` |

---

## Additional Resources

- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Best Practices Guide](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
