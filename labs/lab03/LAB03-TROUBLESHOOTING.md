# LAB03 - Troubleshooting Guide

This document provides solutions to common problems you may encounter while completing LAB03.

## Services Can't Communicate

**Problem**: Frontend shows "Cannot connect to image processor service"

**Solutions**:
1. Verify both services are running: `docker compose ps`
2. Check that services are on the same network in `docker-compose.yml`
3. Verify `PROCESSOR_HOST` is set to the service name (`STUDENTNAME-imgprocessor`), not `localhost` or an IP address
4. Verify `PROCESSOR_GRPC_PORT` is set to `50051` (internal gRPC port, not a public port)
5. Check processor logs: `docker compose logs STUDENTNAME-imgprocessor`
6. Ensure the processor service started successfully before the frontend attempts to connect
7. Verify the frontend has the compiled proto files (`*_pb2.py` and `*_pb2_grpc.py`)

## gRPC Connection Errors

**Problem**: "failed to connect to all addresses", "DNS resolution failed", or "StatusCode.UNAVAILABLE"

**Common Causes and Solutions**:

1. **Wrong hostname**: 
   - ❌ `PROCESSOR_HOST=localhost` or `PROCESSOR_HOST=127.0.0.1`
   - ✅ `PROCESSOR_HOST=STUDENTNAME-imgprocessor` (use the service name from docker-compose.yml)

2. **Wrong port**:
   - ❌ Using public port numbers like 50052
   - ✅ Using internal port `50051` (Docker handles internal routing)

3. **Services not on same network**:
   - Verify docker-compose.yml creates a network
   - Check `docker network ls` and `docker network inspect <network_name>`

4. **Proto file not compiled**:
   - Verify builder stage compiles the proto file
   - Check that `*_pb2.py` and `*_pb2_grpc.py` exist in the container
   - Run: `docker compose exec frontend ls -la` to verify files

5. **Processor not ready**:
   - Check processor logs: `docker compose logs STUDENTNAME-imgprocessor`
   - Verify processor started without errors
   - Add `depends_on` in docker-compose.yml to ensure startup order

## Verifying gRPC Communication

To verify the gRPC connection is working:

```bash
# Check if both services are running
docker compose ps

# View frontend logs for connection attempts
docker compose logs STUDENTNAME-frontend | grep -i grpc

# View processor logs for incoming requests
docker compose logs STUDENTNAME-imgprocessor | grep -i grpc

# Check network connectivity from frontend to processor
docker compose exec frontend ping imgprocessor

# Verify DNS resolution
docker compose exec frontend nslookup imgprocessor
```

## Port Already in Use

**Problem**: `Error starting userland proxy: listen tcp4 0.0.0.0:30090: bind: address already in use`

**Solutions**:
```bash
# Find what's using your assigned port
sudo lsof -i :30090

# Check all Docker containers
docker ps -a

# Stop conflicting containers
docker compose down

# If another student's container is using the port, contact the TA
```

**Port Configuration Rules**:
- Use ports in your assigned range: 30090-30095
- Only frontend needs a public port mapping
- Imgprocessor has NO public ports (internal only)
- Internal ports (8080, 50051) stay the same across all students

## Image Processing Fails

**Problem**: Image upload works but processing returns an error

**Solutions**:
1. Check processor logs: `docker compose logs STUDENTNAME-imgprocessor`
2. Verify the image format is supported (PNG, JPEG)
3. Ensure gRPC communication is working (see "Verifying gRPC Communication" above)
4. For resize, ensure width and height are positive integers
5. For blur, ensure kernel size is odd
6. Check that proto files were compiled correctly in the frontend container

## Build Fails

**Problem**: `docker compose build` fails

**Solutions**:
1. Check Docker is running: `docker ps`
2. Verify Dockerfiles exist in correct locations
3. Check that all referenced files exist (app.py, main.cpp, static/, etc.)
4. Review build logs for specific errors
5. Try building services individually:
   ```bash
   docker build -f frontend/Dockerfile -t STUDENTNAME-frontend .
   docker build -f imgprocessor/Dockerfile -t STUDENTNAME-imgprocessor .
   ```

## Changes Not Reflected

**Problem**: Code changes don't appear after restart

**Solution**: Rebuild the images:
```bash
docker compose down
docker compose up --build
```
