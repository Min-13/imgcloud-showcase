# LAB03 - Understanding Docker Compose

This document provides in-depth information about Docker Compose concepts used in LAB03.

## Service Discovery

Docker Compose automatically sets up DNS so services can find each other by name:
- Frontend connects to processor at `STUDENTNAME-imgprocessor:50051` for gRPC
- Frontend checks processor health at `http://STUDENTNAME-imgprocessor:8080/health`
- No need to use IP addresses
- Service names are resolved automatically within the Docker network
- This only works for internal communication - external users must use public ports (30090-30095)

## Networks

Docker Compose creates a default network for your services:
- All services in the same `docker-compose.yml` are on the same network by default
- Services can communicate using service names for both gRPC and HTTP
- External users connect via published ports:
  - `30090` → Frontend HTTP (web UI) - your assigned port from range 30090-30095
  - Imgprocessor has NO published ports - internal communication only
- Internal communication uses service names:
  - Frontend → Processor: `STUDENTNAME-imgprocessor:50051` (gRPC)
  - Frontend → Processor Health: `http://STUDENTNAME-imgprocessor:8080/health`

## Dependency Management

The `depends_on` directive ensures services start in order:
- Processor starts first
- Frontend starts after processor
- Note: This only waits for the container to start, not for the service to be ready
- Use health checks for more robust startup coordination

## Additional Challenges (Optional)

Want to go further? Try these:

1. **Multiple Processors**: Scale the processor service to multiple instances:
   ```yaml
   imgprocessor:
     # ... existing config ...
     deploy:
       replicas: 3
   ```

2. **Load Balancing**: Add nginx as a reverse proxy to load balance between processor instances

3. **Monitoring**: Add a monitoring service (Prometheus/Grafana) to track request rates and processing times

4. **Caching**: Add Redis to cache processed images and avoid reprocessing

5. **Async Processing**: Modify the architecture to use a message queue (RabbitMQ) for asynchronous processing
