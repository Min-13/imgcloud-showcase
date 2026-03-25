# Docker Cheatsheet

A comprehensive reference for common Docker commands and concepts.

## Table of Contents
- [Basic Commands](#basic-commands)
- [Building Images](#building-images)
- [Running Containers](#running-containers)
- [Managing Containers](#managing-containers)
- [Managing Images](#managing-images)
- [Docker Compose](#docker-compose)
- [Networking](#networking)
- [Volumes](#volumes)
- [Debugging](#debugging)
- [Best Practices](#best-practices)

---

## Basic Commands

```bash
# Check Docker version
docker --version

# Display system-wide information
docker info

# Show Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

---

## Building Images

```bash
# Build an image from a Dockerfile
docker build -t <image-name>:<tag> .

# Build with a specific Dockerfile
docker build -f Dockerfile.dev -t <image-name>:<tag> .

# Build without cache
docker build --no-cache -t <image-name>:<tag> .

# Build with build arguments
docker build --build-arg VERSION=1.0 -t <image-name>:<tag> .

# Show build history of an image
docker history <image-name>

# Tag an image
docker tag <source-image>:<tag> <target-image>:<tag>
```

---

## Running Containers

```bash
# Run a container
docker run <image-name>

# Run in detached mode (background)
docker run -d <image-name>

# Run with a custom name
docker run --name <container-name> <image-name>

# Run and remove container after it stops
docker run --rm <image-name>

# Run with port mapping (host:container)
docker run -p 8080:80 <image-name>

# Run with environment variables
docker run -e ENV_VAR=value <image-name>

# Run with volume mount
docker run -v /host/path:/container/path <image-name>

# Run with interactive terminal
docker run -it <image-name> /bin/bash

# Run with resource limits
docker run --memory="512m" --cpus="1.0" <image-name>

# Example: Run the health check server
docker run -d -p 8080:8080 --name health-server <image-name>
```

---

## Managing Containers

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Start a stopped container
docker start <container-id>

# Stop a running container
docker stop <container-id>

# Restart a container
docker restart <container-id>

# Remove a container
docker rm <container-id>

# Force remove a running container
docker rm -f <container-id>

# View container logs
docker logs <container-id>

# Follow container logs in real-time
docker logs -f <container-id>

# Execute a command in a running container
docker exec -it <container-id> /bin/bash

# Inspect container details
docker inspect <container-id>

# View container resource usage
docker stats <container-id>

# Copy files from container to host
docker cp <container-id>:/path/in/container /path/on/host

# Copy files from host to container
docker cp /path/on/host <container-id>:/path/in/container
```

---

## Managing Images

```bash
# List all images
docker images

# Pull an image from a registry
docker pull <image-name>:<tag>

# Push an image to a registry
docker push <image-name>:<tag>

# Remove an image
docker rmi <image-id>

# Remove all unused images
docker image prune -a

# Save an image to a tar file
docker save -o <filename>.tar <image-name>

# Load an image from a tar file
docker load -i <filename>.tar

# Search for images in Docker Hub
docker search <image-name>
```

---

## Docker Compose

```bash
# Start services defined in docker-compose.yml
docker-compose up

# Start services in detached mode
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs

# View logs for a specific service
docker-compose logs <service-name>

# Build or rebuild services
docker-compose build

# List running services
docker-compose ps

# Execute command in a running service
docker-compose exec <service-name> <command>

# Scale a service
docker-compose up -d --scale <service-name>=3
```

---

## Networking

```bash
# List networks
docker network ls

# Create a network
docker network create <network-name>

# Connect a container to a network
docker network connect <network-name> <container-id>

# Disconnect a container from a network
docker network disconnect <network-name> <container-id>

# Inspect a network
docker network inspect <network-name>

# Remove a network
docker network rm <network-name>

# Run a container with a specific network
docker run --network=<network-name> <image-name>
```

---

## Volumes

```bash
# List volumes
docker volume ls

# Create a volume
docker volume create <volume-name>

# Inspect a volume
docker volume inspect <volume-name>

# Remove a volume
docker volume rm <volume-name>

# Remove all unused volumes
docker volume prune

# Run a container with a named volume
docker run -v <volume-name>:/container/path <image-name>
```

---

## Debugging

```bash
# View detailed container information
docker inspect <container-id>

# Check container logs
docker logs <container-id>

# Access container shell
docker exec -it <container-id> /bin/sh

# View running processes in a container
docker top <container-id>

# Monitor container resource usage
docker stats

# View container port mappings
docker port <container-id>

# Check Docker daemon logs
journalctl -u docker

# Export container filesystem
docker export <container-id> > container.tar
```

---

## Best Practices

### Dockerfile Best Practices

```dockerfile
# 1. Use official base images
FROM node:18-alpine

# 2. Use multi-stage builds to reduce image size
FROM golang:1.21 AS builder
# ... build steps ...
FROM alpine:latest
# ... copy artifacts ...

# 3. Minimize layers by combining commands
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*

# 4. Order instructions from least to most frequently changing
COPY package.json package-lock.json ./
RUN npm install
COPY . .

# 5. Use .dockerignore to exclude unnecessary files
# Create a .dockerignore file similar to .gitignore

# 6. Don't run containers as root
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser
USER appuser

# 7. Use specific tags, not 'latest'
FROM node:18.17.0-alpine

# 8. Add HEALTHCHECK instruction
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# 9. Use environment variables for configuration
ENV PORT=8080
ENV NODE_ENV=production

# 10. Document exposed ports
EXPOSE 8080
```

### Security Best Practices

```bash
# Scan images for vulnerabilities
docker scan <image-name>

# Run containers with read-only filesystem
docker run --read-only <image-name>

# Drop unnecessary capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE <image-name>

# Use secrets for sensitive data (Docker Swarm)
docker secret create my_secret secret.txt
docker service create --secret my_secret <image-name>

# Limit resources
docker run --memory="256m" --cpus="0.5" <image-name>
```

### Performance Tips

```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker build -t <image-name> .

# Cache dependencies in separate layer
# In Dockerfile:
COPY package.json package-lock.json ./
RUN npm install
COPY . .

# Use .dockerignore to reduce build context
# In .dockerignore:
node_modules
.git
*.md
```

---

## Common Patterns

### Development Workflow

```bash
# Build the image
docker build -t my-app:dev .

# Run with volume mount for live reloading
docker run -p 8080:8080 -v $(pwd):/app my-app:dev

# View logs
docker logs -f <container-id>

# Execute commands for debugging
docker exec -it <container-id> /bin/bash
```

### Testing the Health Server

```bash
# Build the image
docker build -t health-server:latest .

# Run the container
docker run -d -p 8080:8080 --name health-test health-server:latest

# Test the health endpoint
curl http://localhost:8080/health

# View logs
docker logs health-test

# Stop and remove
docker stop health-test && docker rm health-test
```

---

## Troubleshooting

### Common Issues

```bash
# Container exits immediately
# Check logs: docker logs <container-id>
# Run interactively: docker run -it <image-name> /bin/sh

# Port already in use
# Check: netstat -tulpn | grep <port>
# Use different port: docker run -p 9090:8080 <image-name>

# Permission denied errors
# Check user: docker exec -it <container-id> whoami
# Check file permissions: docker exec -it <container-id> ls -la

# Cannot connect to Docker daemon
sudo systemctl start docker
sudo usermod -aG docker $USER

# Out of disk space
docker system prune -a
docker volume prune
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `docker build -t name .` | Build image |
| `docker run -d -p 8080:80 name` | Run container |
| `docker ps` | List running containers |
| `docker logs <id>` | View logs |
| `docker exec -it <id> bash` | Access container |
| `docker stop <id>` | Stop container |
| `docker rm <id>` | Remove container |
| `docker images` | List images |
| `docker rmi <id>` | Remove image |
| `docker-compose up -d` | Start services |

---

## Additional Resources

- [Official Docker Documentation](https://docs.docker.com/)
- [Docker Hub](https://hub.docker.com/)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices Guide](https://docs.docker.com/develop/dev-best-practices/)
