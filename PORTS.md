# Port Assignments for CSC420 Students

This document assigns port ranges to each student for running their Docker containers. Each student has been allocated a range of 10 ports in the 30000-30100 range.

## Port Range Assignments

| Student      | Port Range       | Starting Port | Ending Port |
|--------------|------------------|---------------|-------------|
| idominguez   | 30000-30009      | 30000         | 30009       |
| igarrelts    | 30010-30019      | 30010         | 30019       |
| jhelsley     | 30020-30029      | 30020         | 30029       |
| amedrano     | 30030-30039      | 30030         | 30039       |
| lmolitor     | 30040-30049      | 30040         | 30049       |
| bstempowski  | 30050-30059      | 30050         | 30059       |
| mthawzin     | 30060-30069      | 30060         | 30069       |
| mtorres      | 30070-30079      | 30070         | 30079       |

## Docker Port Mapping

When running Docker containers, you need to map a port from the host machine to the container's exposed port. The image processing service typically runs on port 8080 inside the container.

### Basic Port Mapping Syntax

```bash
docker run -p <HOST_PORT>:<CONTAINER_PORT> <IMAGE_NAME>
```

Where:
- `<HOST_PORT>` is the port on your host machine (use your assigned range)
- `<CONTAINER_PORT>` is the port the application listens on inside the container (typically 8080)
- `<IMAGE_NAME>` is the name of your Docker image

### Example

```bash
# Map host port 30090 to container port 8080
docker run -p 30090:8080 jwilson-imgcloud

# Access the service at:
# http://localhost:30090
```

**Note:** Replace `jwilson` with your username and `30090` with a port from your assigned range.

## Complete Docker Run Example

Here's a complete example with common options:

```bash
docker run \
  --name jwilson-imgcloud \
  -p 30090:8080 \
  -d \
  jwilson-imgcloud
```

Options explained:
- `--name jwilson-imgcloud` - Assign a name to the container for easy reference
- `-p 30090:8080` - Map port 30090 on host to port 8080 in container
- `-d` - Run in detached mode (background)
- `jwilson-imgcloud` - The image name (replace with your username-imgcloud)

## Multiple Services

If you need to run multiple containers simultaneously (e.g., both Python and Go versions), use different ports from your range:

```bash
# Run Python version on first port
docker run --name jwilson-imgcloud-python -p 30090:8080 -d jwilson-imgcloud-python

# Run Go version on second port
docker run --name jwilson-imgcloud-go -p 30091:8080 -d jwilson-imgcloud-go
```

## Checking Running Containers

To see which ports are currently in use:

```bash
# List all running containers with their port mappings
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
```

## Stopping and Removing Containers

```bash
# Stop a running container
docker stop jwilson-imgcloud

# Remove a stopped container
docker rm jwilson-imgcloud

# Stop and remove in one command
docker rm -f jwilson-imgcloud
```

## Port Conflicts

If you get a "port is already allocated" error:

1. Check if another container is using the port:
   ```bash
   docker ps | grep 30090
   ```

2. Check if another process is using the port:
   ```bash
   sudo lsof -i :30090
   # or
   sudo netstat -tulpn | grep 30090
   ```

3. Use a different port from your assigned range:
   ```bash
   docker run -p 30091:8080 jwilson-imgcloud
   ```

## Best Practices

1. **Use your assigned range only** - This prevents conflicts with other students
2. **Document which ports you're using** - Keep track of which services use which ports
3. **Clean up unused containers** - Run `docker container prune` periodically
4. **Use meaningful container names** - Makes it easier to manage multiple containers
5. **Check for conflicts before starting** - Ensure the port isn't already in use

## Additional Resources

- [Docker run reference](https://docs.docker.com/engine/reference/run/)
- [Docker port mapping documentation](https://docs.docker.com/config/containers/container-networking/)
- [Docker container networking](https://docs.docker.com/network/)
