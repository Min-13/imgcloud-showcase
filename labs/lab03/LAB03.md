# LAB03: Multi-Container Image Processing with Docker Compose

## Overview

This lab demonstrates a microservices architecture where image processing is separated into two distinct services:

1. **Frontend Service** (Python/Flask) - Provides the web interface and API endpoints
2. **Image Processor Service** (C++) - Performs expensive image processing operations

The frontend communicates with the image processor using **gRPC** (a high-performance RPC framework), while maintaining HTTP for health checks. Both services are orchestrated using Docker Compose.

**Supporting Documentation:**
- [LAB03-BACKGROUND.md](LAB03-BACKGROUND.md) - Why gRPC? Architecture overview, design rationale, learning objectives
- [LAB03-OPERATIONS.md](LAB03-OPERATIONS.md) - Detailed list of image processing operations
- [LAB03-COMMUNICATION.md](LAB03-COMMUNICATION.md) - Protocol Buffers, gRPC communication details
- [LAB03-TROUBLESHOOTING.md](LAB03-TROUBLESHOOTING.md) - Common problems and solutions
- [LAB03-UNDERSTANDING.md](LAB03-UNDERSTANDING.md) - Deep dive into Docker Compose concepts
- [LAB03-REVIEW.md](LAB03-REVIEW.md) - Detailed Dockerfile reviews for both services

## Lab Requirements

### Your Tasks

For this lab, you need to create a `docker-compose.yml` file that orchestrates both the frontend and image processor services.

**Before you begin**, review the Dockerfiles for both services to understand how they work. See [LAB03-REVIEW.md](LAB03-REVIEW.md) for detailed explanations of:
- Frontend Dockerfile structure (multi-stage build, proto compilation)
- Image Processor Dockerfile structure (C++ service with gRPC and HTTP)

## Step-by-Step Docker Compose Setup

To help you build and test your docker-compose.yml incrementally, follow these logical steps. This approach allows you to verify each component works before connecting them together.

### Step 1: Set Up the Network Configuration

Start by setting up the custom Docker network in your `docker-compose.yml`:

```yaml
networks:
  STUDENTNAME-network:  # Replace STUDENTNAME with your username
    driver: bridge
```

**Why start with networking?**
- Networks must be defined before services can reference them
- Using a custom network with your STUDENTNAME ensures isolation from other students on the shared VPS
- The network allows services to communicate using service names as hostnames

### Step 2: Add the Image Processor Service

Add the imgprocessor service to your `docker-compose.yml`. Your imgprocessor service needs:
- A service name including your STUDENTNAME (e.g., `STUDENTNAME-imgprocessor`)
- Build configuration:
  - `context: .` (the build context - the directory Docker uses to find files referenced in the Dockerfile; `.` means the project root)
  - `dockerfile: imgprocessor/Dockerfile` (path to the Dockerfile relative to the context)
- A container name matching your service name
- Connection to the `STUDENTNAME-network`
- Environment variables:
  - `HTTP_PORT=8080`
  - `GRPC_PORT=50051`
- **NO public port mappings** (internal communication only)

**Test commands:**

```bash
# Start only the imgprocessor
docker compose up STUDENTNAME-imgprocessor --build -d

# Check if it's running
docker compose ps

# Check the logs
docker compose logs STUDENTNAME-imgprocessor
```

**Expected behavior:**
- Imgprocessor container starts successfully
- Logs show "HTTP server listening on port 8080"
- Logs show "gRPC server listening on port 50051"
- No error messages in the logs

**Note:** The imgprocessor health endpoint is NOT publicly accessible from your host machine. It only responds on the internal Docker network. You'll verify it's reachable in the next step.

**Once verified, stop the processor:**
```bash
docker compose down
```

### Step 3: Add the Frontend Service

Add your frontend service to the `docker-compose.yml`. Your frontend service needs:
- A service name including your STUDENTNAME (e.g., `STUDENTNAME-frontend`)
- Build configuration:
  - `context: .` (the build context - the directory Docker uses to find files referenced in the Dockerfile; `.` means the project root)
  - `dockerfile: frontend/Dockerfile` (path to the Dockerfile relative to the context)
- A container name matching your service name
- Port mapping from your assigned port to container port 8080 (format: `"YOUR_PORT:8080"`)
- Connection to the `STUDENTNAME-network`
- Environment variables:
  - `PORT=8080`
  - `PROCESSOR_HOST=STUDENTNAME-imgprocessor` (must match imgprocessor service name)
  - `PROCESSOR_GRPC_PORT=50051`
  - `PROCESSOR_HTTP_PORT=8080`
- `depends_on` to ensure imgprocessor starts first

**Test commands:**

```bash
# Build and start just the frontend
docker compose up STUDENTNAME-frontend --build -d

# Check if it's running
docker compose ps

# Test the health endpoint
curl http://localhost:YOUR_PORT/health

# Test in browser
# Navigate to http://csc.wils.one:YOUR_PORT
```

**Expected behavior:**
- Frontend container starts successfully
- Web UI is accessible in your browser
- If imgprocessor is not running, health endpoint returns `"status":"degraded"` with `"processor":"unavailable"`

**Once verified, stop the frontend:**
```bash
docker compose down
```

### Step 4: Test Both Services Together

Now that you've tested each service independently, start both services together:

**Test commands:**

```bash
# Start both services
docker compose up --build -d

# Check both are running
docker compose ps

# Test the health endpoint - should now show "healthy"
curl http://localhost:YOUR_PORT/health

# View logs from both services
docker compose logs -f
```

**Expected behavior:**
- Both containers start successfully
- Frontend health shows `"status":"healthy"` with `"processor":"healthy"`
- No connection errors in the logs
- Services can communicate on the Docker network

**Test image processing in your browser:**

1. Navigate to `http://csc.wils.one:YOUR_PORT`
2. Upload a test image
3. Select an operation (e.g., "Grayscale")
4. Click "Process Image"
5. Verify the processed image is returned

**Success indicators:**
- ✅ Health check shows both services healthy
- ✅ Image upload and processing works
- ✅ No gRPC connection errors in logs
- ✅ Processed image displays in browser

**If it doesn't work:** See [LAB03-TROUBLESHOOTING.md](LAB03-TROUBLESHOOTING.md) and verify:
- Both services are on the same network
- `PROCESSOR_HOST` exactly matches your imgprocessor service name
- No typos in service names or environment variables
- Imgprocessor started before frontend attempted to connect

**When done testing:**
```bash
docker compose down
```

### Key Configuration Checklist

Before submitting, verify your `docker-compose.yml` includes:
- ✅ Custom network with unique name (`STUDENTNAME-network`)
- ✅ Both services connected to the same network
- ✅ Frontend has public port mapping (YOUR_PORT:8080)
- ✅ Imgprocessor has NO public ports
- ✅ `PROCESSOR_HOST` matches imgprocessor service name exactly
- ✅ `depends_on` ensures imgprocessor starts before frontend
- ✅ All environment variables set correctly
- ✅ Unique service/container names with your STUDENTNAME

For detailed information about Docker Compose configuration options, see [DOCKER-COMPOSE.md](DOCKER-COMPOSE.md).

For a deeper understanding of Docker Compose networking concepts, see [LAB03-UNDERSTANDING.md](LAB03-UNDERSTANDING.md).

## Building and Running with Docker Compose

### Start All Services

```bash
# Start in detached mode (background)
docker compose up --build -d

# Or start with logs visible (foreground)
docker compose up --build
```

**Note:** The `--build` flag ensures images are rebuilt if code changes. Without it, Docker uses cached images.

### Access Your Application

Once running, access your application:
- **Web UI**: `http://csc.wils.one:YOUR_PORT` (replace YOUR_PORT with your assigned port from PORTS.md)
- **Health Check**: `curl http://localhost:YOUR_PORT/health` or `http://csc.wils.one:YOUR_PORT/health`

### View Logs

```bash
# View logs from all services
docker compose logs

# View logs from a specific service
docker compose logs STUDENTNAME-frontend
docker compose logs STUDENTNAME-imgprocessor

# Follow logs in real-time
docker compose logs -f

# Show only recent logs
docker compose logs --tail=50 -f
```

### Stop All Services

```bash
docker compose down
```

This stops and removes the containers but keeps the images.

## Cleanup

Since you are working on a shared VPS, it's important to clean up your resources after testing:

```bash
# Stop and remove containers, networks, and volumes
docker compose down

# Remove volumes (if any were created)
docker compose down -v

# View remaining resources
docker ps -a
docker images
docker network ls

# Optional: Remove dangling images to free space
docker image prune -f
```

**Important Cleanup Rules**:
- Always run `docker compose down` when finished with testing
- Clean up promptly to free resources for other students
- Images are automatically tagged by Docker Compose based on directory name
- Don't leave containers running when not actively testing

### Rebuild After Code Changes

```bash
docker compose down
docker compose up --build
```

**Why always use Docker Compose?**
- Ensures consistent environment across all deployments
- Handles networking and service discovery automatically
- Prevents port conflicts on shared VPS
- Matches production deployment patterns
- Makes cleanup easier with a single command

## Testing Your Implementation

### 1. Check Services Are Running

```bash
docker compose ps
```

You should see both `STUDENTNAME-frontend` and `STUDENTNAME-imgprocessor` services running.

### 2. Test Health Endpoints

```bash
# Test frontend health (HTTP) - publicly accessible
curl http://localhost:YOUR_PORT/health
```

Should return JSON with `"status": "healthy"`.

**Note**: The processor health endpoint is NOT publicly accessible. It only responds to health checks from within the Docker network (e.g., from the frontend service). This is intentional for security - internal services should not be directly exposed to the public internet.

### 3. Test via Web Browser

1. Open your web browser
2. Navigate to `http://csc.wils.one:YOUR_PORT` (replace YOUR_PORT with your assigned port)
3. You should see the "Image Processing Service" web interface
4. Upload an image using the file selector
5. Select an operation from the dropdown
6. Fill in any required parameters (e.g., width/height for resize, angle for rotate)
7. Click "Process Image"
8. The processed image should appear below
9. Download the processed image if desired

### 4. Test All Operations

Try each operation to verify they work:

**Resize**:
- Upload an image
- Select "Resize"
- Enter width: 200, height: 200
- Click "Process Image"
- Verify the image is resized

**Grayscale**:
- Upload an image
- Select "Grayscale"
- Click "Process Image"
- Verify the image is converted to grayscale

**Blur**:
- Upload an image
- Select "Blur"
- Enter kernel size: 15 (must be odd)
- Click "Process Image"
- Verify the image is blurred

**Edge Detection**:
- Upload an image
- Select "Edge Detection"
- Click "Process Image"
- Verify edges are detected

**Rotate** (NEW):
- Upload an image
- Select "Rotate"
- Enter angle: 90 (degrees)
- Click "Process Image"
- Verify the image is rotated 90 degrees

**Mirror** (NEW):
- Upload an image
- Select "Mirror"
- Choose direction: Horizontal or Vertical
- Click "Process Image"
- Verify the image is mirrored in the selected direction

### 5. Test with Command Line (Optional)

You can test the web API using curl (note: this uses HTTP to communicate with the frontend, but the frontend uses gRPC to communicate with the processor):

```bash
# Replace YOUR_PORT with your assigned port

# Resize operation
curl -F "image=@test.png" -F "operation=resize" -F "width=200" -F "height=200" \
  http://localhost:YOUR_PORT/process -o output.png

# Rotate operation
curl -F "image=@test.png" -F "operation=rotate" -F "angle=45" \
  http://localhost:YOUR_PORT/process -o rotated.png

# Mirror operation
curl -F "image=@test.png" -F "operation=mirror" -F "direction=horizontal" \
  http://localhost:YOUR_PORT/process -o mirrored.png
```

**Architecture Note**: While you're using HTTP/curl to talk to the frontend, behind the scenes the frontend is using gRPC to communicate with the image processor. This is a common pattern where external APIs use HTTP/REST for compatibility, but internal service-to-service communication uses gRPC for performance.

## Submission

When submitting your lab:

1. Create and include your `docker-compose.yml` in your repository
2. Tag your final submission:
   ```bash
   git add docker-compose.yml
   git commit -m "Complete Lab03"
   git tag lab03-final
   git push origin main --tags
   ```

Your submission should include only:
- `docker-compose.yml` - Your orchestration file for both services

**Note:** The `frontend/Dockerfile` is provided for you and should not be modified or submitted.

## Summary

This lab demonstrates a practical microservices architecture where:
- The frontend (Python) handles user interaction and routing
- The processor (C++) performs computationally expensive operations
- Services communicate via **gRPC** using Protocol Buffers for efficiency and type safety
- HTTP is maintained for health checks (simplicity and monitoring compatibility)
- Docker Compose orchestrates multiple containers with automatic networking
- Environment variables configure service locations and ports
- **Only the frontend is publicly accessible** (port 30090-30095 range)
- **Internal services communicate via Docker network** (imgprocessor not exposed)
- Proto files are compiled during Docker build for reproducibility
- Each service can be developed, deployed, and scaled independently

For a deeper understanding of these concepts, see [LAB03-BACKGROUND.md](LAB03-BACKGROUND.md).
