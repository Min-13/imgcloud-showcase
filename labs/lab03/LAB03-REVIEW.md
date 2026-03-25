# LAB03 - Dockerfile Review

This document provides detailed information about the Dockerfiles used in this lab.

## Frontend Dockerfile Review

**Note: The frontend uses Python exclusively.** Unlike LAB02 where you could choose between Python or Go, LAB03 focuses on Python for the frontend to provide a consistent learning experience with gRPC integration.

A Dockerfile has been provided in the `frontend/` directory (`frontend/Dockerfile`). You should review it to understand how it:
- Uses a **multi-stage build** (builder stage + runtime stage)
- Installs gRPC dependencies: `grpcio`, `grpcio-tools`, `protobuf`
- Installs other Python dependencies from `requirements.txt`
- **Copies the proto file** from `imgprocessor/image_processor.proto`
- **Compiles the proto file** to Python code in the builder stage
- Copies the generated Python files (`*_pb2.py`, `*_pb2_grpc.py`) to the runtime stage
- Copies the application code (`app.py`)
- Copies the `static/` directory for the web UI
- Runs as a non-root user for security
- Exposes port 8080 (for HTTP web UI)
- Sets default environment variables for processor communication (you'll override these in docker-compose.yml)

### Understanding the Dockerfile Structure

The provided Dockerfile follows this structure:

#### 1. Builder Stage (compile proto files)

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app

# Install grpc tools for proto compilation
RUN pip install --no-cache-dir grpcio-tools

# IMPORTANT: Copy proto file from imgprocessor directory (not frontend)
# The proto file is located at: imgprocessor/image_processor.proto
COPY imgprocessor/image_processor.proto .

# Compile proto file to Python
# This generates two files: image_processor_pb2.py and image_processor_pb2_grpc.py
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. image_processor.proto
```

**What gets generated?**
- `image_processor_pb2.py`: Protocol buffer message definitions
- `image_processor_pb2_grpc.py`: gRPC client/server stub code

These generated files are copied to the runtime stage.

#### 2. Runtime Stage (the application)

- Starts with `python:3.11-slim`
- Sets working directory to `/home/appuser/app`
- Copies and installs dependencies from `frontend/requirements.txt`
- **Copies compiled proto files from builder stage**:
  ```dockerfile
  COPY --from=builder /app/image_processor_pb2.py .
  COPY --from=builder /app/image_processor_pb2_grpc.py .
  ```
- Copies application code (`frontend/app.py`)
- Copies static directory for the web UI
- Creates and switches to non-root user for security
- Sets default environment variables (can be overridden in docker-compose.yml)
- Exposes port 8080
- Runs the application with `CMD ["python", "app.py"]`

### Why Multi-Stage Build?

- **Smaller images**: Build tools (grpcio-tools) not included in final image
- **Security**: Separate build and runtime concerns
- **Single Source of Truth**: Proto file lives in imgprocessor/, frontend copies and compiles it during build
- **Best practice**: Standard pattern for production Docker images

### Key Points

- `requirements.txt` includes: `grpcio`, `protobuf` (grpcio-tools only needed in builder)
- Proto file is copied from `imgprocessor/` directory during build
- Generated `*_pb2.py` and `*_pb2_grpc.py` files are available to `app.py`
- Environment variables can be overridden in your `docker-compose.yml`

For more details on how services communicate, see [LAB03-COMMUNICATION.md](LAB03-COMMUNICATION.md).

## Image Processor Dockerfile Review

The image processor Dockerfile is already provided in `imgprocessor/Dockerfile`. You should:
- Review it to understand how the C++ service is built
- Note that it uses OpenCV for image processing and gRPC for service communication
- Understand that it exposes:
  - Port 50051 for gRPC (image processing operations)
  - Port 8080 for HTTP (health checks only)
- **Important**: In docker-compose.yml, imgprocessor should have NO public port mappings
  - It only communicates internally on the Docker network
  - Frontend accesses it at `STUDENTNAME-imgprocessor:50051` (gRPC) and `STUDENTNAME-imgprocessor:8080` (HTTP health)
- **Do not modify this Dockerfile** - it's provided for you
