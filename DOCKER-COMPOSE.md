# Docker Compose Reference for Lab 03

This document describes the Docker Compose fields and configuration needed for Lab 03.

## Overview

Docker Compose is a tool for defining and running multi-container Docker applications. You use a YAML file (`docker-compose.yml`) to configure your application's services, networks, and volumes.

## Required Fields for Lab 03

### Top-Level Structure

```yaml
version: '3.8'

services:
  # Service definitions go here

networks:
  # Network definitions go here
```

- **version**: Specifies the Docker Compose file format version. Use `'3.8'` for this lab.
- **services**: Defines all the containers that make up your application
- **networks**: Defines custom networks for container communication

## Service Configuration

Each service (container) requires these key fields:

### Basic Service Fields

```yaml
services:
  service-name:
    build:
      context: .
      dockerfile: path/to/Dockerfile
    container_name: unique-container-name
    ports:
      - "PUBLIC_PORT:INTERNAL_PORT"
    environment:
      - VAR_NAME=value
    depends_on:
      - other-service
    networks:
      - network-name
```

### Field Descriptions

#### `build`
Specifies how to build the Docker image for this service.

- **context**: The build context (usually `.` for the repository root)
- **dockerfile**: Path to the Dockerfile relative to the context

Example:
```yaml
build:
  context: .
  dockerfile: frontend/Dockerfile
```

#### `container_name`
Gives the container a specific name. This is useful for:
- Identifying containers with `docker ps`
- Debugging and logs
- Network communication (containers can reach each other by name)

Example:
```yaml
container_name: frontend
```

#### `ports`
Maps ports from the host machine to the container.

Format: `"HOST_PORT:CONTAINER_PORT"`

**Important for Lab 03:**
- Use your assigned port range (see PORTS.md file for your specific range)
- Only expose ports that need external access
- Internal services (like imgprocessor) don't need public ports

Example:
```yaml
ports:
  - "30000:8080"  # Maps your assigned public port to container's internal port 8080
```

#### `environment`
Sets environment variables inside the container.

These are used by your application to configure behavior at runtime.

Example:
```yaml
environment:
  - PORT=8080
  - PROCESSOR_HOST=imgprocessor
  - PROCESSOR_HTTP_PORT=8080
  - PROCESSOR_GRPC_PORT=50051
```

**Common environment variables for Lab 03:**
- `PORT`: The port your service listens on internally
- `PROCESSOR_HOST`: Hostname of the image processor (use container name)
- `PROCESSOR_HTTP_PORT`: Port for HTTP health checks (8080)
- `PROCESSOR_GRPC_PORT`: Port for gRPC communication (50051)

#### `depends_on`
Specifies which services must start before this one.

Example:
```yaml
depends_on:
  - imgprocessor  # Start imgprocessor before frontend
```

**Note**: This only controls startup order, not readiness. The frontend should handle cases where the processor isn't immediately available.

#### `networks`
Specifies which networks this service connects to.

Example:
```yaml
networks:
  - imgcloud
```

## Network Configuration

Define custom networks for container communication:

```yaml
networks:
  imgcloud:
    driver: bridge
```

- **driver**: Network driver type. Use `bridge` for containers on the same host.

### How Container Networking Works

When containers are on the same network:
1. They can communicate using container names as hostnames
2. Example: Frontend can reach imgprocessor at `http://imgprocessor:8080`
3. Internal ports are accessible without port mapping
4. Only services with `ports` mappings are accessible from outside

## Complete Example for Lab 03

```yaml
version: '3.8'

services:
  # Image processor - internal only, no public ports
  imgprocessor:
    build:
      context: .
      dockerfile: imgprocessor/Dockerfile
    container_name: imgprocessor
    environment:
      - HTTP_PORT=8080
      - GRPC_PORT=50051
    networks:
      - imgcloud

  # Frontend - publicly accessible
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    container_name: frontend
    ports:
      - "30090:8080"  # Use your assigned port range
    environment:
      - PORT=8080
      - PROCESSOR_HOST=imgprocessor
      - PROCESSOR_HTTP_PORT=8080
      - PROCESSOR_GRPC_PORT=50051
    depends_on:
      - imgprocessor
    networks:
      - imgcloud

networks:
  imgcloud:
    driver: bridge
```

## Port Assignment Guidelines

**For this lab on shared VPS:**
- Use your assigned port range: **30090-30095**
- Only expose the frontend service publicly
- The imgprocessor service remains internal (no public ports)
- Internal communication uses container names and internal ports

Example port mappings:
- Frontend: `30090:8080` (your public port 30090 → internal 8080)
- Imgprocessor: No port mapping (internal only)

## Testing Your Configuration

1. **Build and start services:**
   ```bash
   docker compose up --build
   ```

2. **Check running containers:**
   ```bash
   docker compose ps
   ```

3. **View logs:**
   ```bash
   docker compose logs -f
   ```

4. **Test the frontend:**
   ```bash
   curl http://localhost:30090/health
   ```

5. **Stop services:**
   ```bash
   docker compose down
   ```

## Common Issues

### Container can't reach another service
- Verify both services are on the same network
- Use the container name (not localhost) as hostname
- Check that the target service is running

### Port already in use
- Another container or process is using your public port
- Use `docker compose down` to stop old containers
- Check with `docker ps -a` and remove old containers

### Build errors
- Check Dockerfile path in `dockerfile` field
- Verify `context` is set correctly (usually `.`)
- Check that all referenced files exist

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Networking in Compose](https://docs.docker.com/compose/networking/)
