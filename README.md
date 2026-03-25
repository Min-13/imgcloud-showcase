# CSC420-2526S-ImgCloud

## Project Overview

ImgCloud is a containerized image processing service designed to help students learn Docker and microservices architecture. The course progresses through multiple labs, each building on the previous:


- **LAB02**: Basic Docker containerization and multi-stage builds
- **LAB03**: Multi-container microservices with gRPC communication
- **LAB04**: Persistent storage, state management, and databases
- **LAB05**: Database connections, caching, and admin interfaces
- **LAB06**: Continuous Integration with GitHub Actions
- **Lab07**: Horizontal Scaling and TLS Termination

All lab instructions are located in the `labs/` directory.

<<<<<<< HEAD
## Current Architecture
=======
## Current Architecture (Lab 04)
>>>>>>> 1d017f9 (Copied and Showcase My Work with Other Teammates in Cloud Environment.)

```
User Browser → Frontend (Python/Flask)
                ↓
           PostgreSQL (shared)
           MinIO (object storage)
           Redis (cache/sessions)
                ↓
           gRPC (port 50051)
                ↓
       Image Processor (C++)
```

**Services:**
1. **Frontend** - Python/Flask web UI with authentication and storage
2. **Image Processor** - C++ gRPC service for image operations
3. **PostgreSQL** - Shared relational database (instructor-managed)
4. **MinIO** - S3-compatible object storage (per-student)
5. **Redis** - Cache and session store (per-student)

## Image Processing Operations

### Supported Operations

1. **Resize** - Resize images to specified dimensions
2. **Grayscale Filter** - Convert images to grayscale using OpenCV
3. **Blur Filter** - Apply Gaussian blur to images using OpenCV
4. **Edge Detection** - Detect edges in images using OpenCV's Canny algorithm
5. **Rotate** (NEW in Lab 03) - Rotate image by specified angle in degrees
6. **Mirror** (NEW in Lab 03) - Mirror image horizontally or vertically

## Technologies

### Frontend (Python/Flask)
- **Flask 3.0.0** - Web framework for the RESTful API and UI
- **grpcio ≥1.60.0** - Python gRPC library for client communication
- **grpcio-tools ≥1.60.0** - Tools for compiling protobuf definitions

### Image Processor (C++)
- **OpenCV 4.x** - Advanced image processing and computer vision operations
- **gRPC C++** - High-performance RPC framework
- **Protocol Buffers** - Efficient binary serialization
- **C++11** - High-performance implementation of image operations

## API Endpoints

### GET /
Root endpoint displaying service information and available operations.

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Service is running"
}
```

### GET /operations
Lists all available image processing operations with their parameters.

**Response:**
```json
{
  "operations": [
    {
      "name": "resize",
      "description": "Resize image to specified dimensions",
      "parameters": ["width", "height"],
      "library": "Pillow"
    },
    ...
  ]
}
```

### POST /process
Process an image with the specified operation.

**Request:** multipart/form-data
- `image` (file, required): Image file to process
- `operation` (string, required): Operation to perform (resize, grayscale, blur, edge_detection, rotate, mirror)
- `width` (integer, optional): Target width for resize operation
- `height` (integer, optional): Target height for resize operation
- `kernel_size` (integer, optional): Kernel size for blur operation (default: 5, must be odd)
- `angle` (integer, optional): Rotation angle in degrees for rotate operation
- `direction` (string, optional): Mirror direction for mirror operation ("horizontal" or "vertical")

**Response:** Processed image as PNG

**Note:** The frontend receives HTTP requests from users, then forwards processing requests to the image processor via gRPC for efficient binary communication.

**Examples:**

```bash
# Resize an image
curl -F "image=@input.png" -F "operation=resize" -F "width=200" -F "height=200" \
  http://localhost:8080/process -o output.png

# Apply grayscale filter
curl -F "image=@input.png" -F "operation=grayscale" \
  http://localhost:8080/process -o output.png

# Apply blur filter
curl -F "image=@input.png" -F "operation=blur" -F "kernel_size=5" \
  http://localhost:8080/process -o output.png

# Apply edge detection
curl -F "image=@input.png" -F "operation=edge_detection" \
  http://localhost:8080/process -o output.png

# Rotate image
curl -F "image=@input.png" -F "operation=rotate" -F "angle=90" \
  http://localhost:8080/process -o output.png

# Mirror image horizontally
curl -F "image=@input.png" -F "operation=mirror" -F "direction=horizontal" \
  http://localhost:8080/process -o output.png
```

**Architecture Note:** These curl commands use HTTP to communicate with the frontend, but the frontend uses gRPC to communicate with the image processor. This is a common pattern where external APIs remain HTTP/REST for compatibility, while internal service communication uses gRPC for performance.

## Running the Service (Lab 03)

### Using Docker Compose (Recommended)

The easiest way to run the complete system is with Docker Compose:

```bash
# Build and start all services
docker compose up --build

# Or run in detached mode
docker compose up -d --build

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

The frontend will be available at `http://localhost:30090` (or your assigned port) for public access.

**Note**: Services run inside Docker containers. Direct access to individual services from the host is not required for this lab. Communication between services happens through the Docker network.

## Multi-Container Architecture (Lab 03)

This lab demonstrates a modern microservices architecture where:

- **Frontend Service**: Lightweight Python/Flask service that handles HTTP requests and serves the web UI
- **Image Processor Service**: High-performance C++ service that performs computationally expensive image operations
- **Communication**: Services communicate via gRPC (binary protocol) for efficiency
- **Health Checks**: HTTP endpoints maintained for simple monitoring
- **Orchestration**: Docker Compose manages both services and their networking

### Benefits of This Architecture

1. **Separation of Concerns**: UI/API handling separate from heavy computation
2. **Performance**: C++ for compute-intensive operations, Python for web serving
3. **Modern RPC**: gRPC provides type safety, streaming, and better performance than HTTP/JSON
4. **Scalability**: Services can be scaled independently
5. **Technology Choice**: Use the best language for each task
6. **Production Pattern**: Matches real-world microservices architectures

### gRPC vs HTTP

This architecture uses both protocols strategically:
- **gRPC (port 50051)**: For image processing operations
  - Binary protocol (protobuf) is efficient for large images
  - Type-safe contracts defined in `.proto` files
  - Streaming support for large data transfers
- **HTTP (port 8080)**: For health checks and user-facing web UI
  - Simple curl testing
  - Compatible with standard monitoring tools
  - Easy debugging and troubleshooting

## Project Structure

```
.
├── labs/                      # Lab instructions
│   ├── lab02/                # Lab 2: Multi-stage builds
│   ├── lab03/                # Lab 3: Microservices & gRPC
│   ├── lab04/                # Lab 4: Storage & databases
│   └── lab05/                # Lab 5: Database connections & caching
├── admin/                     # Admin interface (LAB05)
│   ├── python/               # Python implementation
│   │   ├── app.py            # Flask application
│   │   ├── db.py             # Database connection module
│   │   ├── cache.py          # Redis cache module
│   │   └── static/           # Web UI
│   ├── php/                  # PHP implementation
│   │   ├── index.php         # PHP application
│   │   ├── db.php            # Database connection module
│   │   ├── cache.php         # Redis cache module
│   │   └── static/           # Web UI
│   └── cpp/                  # C++ implementation
│       ├── main.cpp          # HTTP server and endpoints
│       ├── db.h              # Database connection module
│       ├── cache.h           # Redis cache module
│       └── static/           # Web UI
├── frontend/                  # Python Flask frontend service
│   ├── app.py                # Application with LAB03 & LAB04 support
│   ├── Dockerfile            # Container definition
│   ├── requirements.txt      # Python dependencies
│   └── test_*.py             # Unit tests
├── imgprocessor/             # C++ image processing service
│   ├── main.cpp              # gRPC server entry point
│   ├── grpc_server.cpp       # gRPC service implementation
│   ├── http_server.cpp       # HTTP health check server
│   ├── image_processor.cpp   # OpenCV image operations
│   ├── image_processor.proto # Protocol Buffers definition
│   ├── Makefile              # Build configuration
│   └── Dockerfile            # Processor container definition
├── cpp-lib/                  # Shared C++ library (LAB02)
├── static/                   # Web UI (HTML/CSS/JS)
├── PORTS.md                  # Port assignments
├── DOCKERFILE_CHEATSHEET.md  # Dockerfile reference
├── DOCKER_CHEATSHEET.md      # Docker CLI reference
├── DOCKER-COMPOSE.md         # Docker Compose guide
└── README.md                 # This file
```

## Labs

All lab instructions are in the `labs/` directory:

- **[labs/lab02/](labs/lab02/)** - Multi-stage Docker builds and C++ integration
  - [LAB02.md](labs/lab02/LAB02.md) - Main lab instructions

- **[labs/lab03/](labs/lab03/)** - Multi-container microservices with gRPC
  - [LAB03.md](labs/lab03/LAB03.md) - Main lab instructions
  - Supporting documentation on gRPC, Docker Compose, and troubleshooting
  
- **[labs/lab04/](labs/lab04/)** - Persistent storage and state management
  - [LAB04.md](labs/lab04/LAB04.md) - Main lab instructions
  - Supporting documentation on MinIO, PostgreSQL, Redis, and caching

- **[labs/lab05/](labs/lab05/)** - Database connections, caching, and admin interfaces
  - [LAB05.md](labs/lab05/LAB05.md) - Main lab instructions
  - Multiple language implementations: Python, PHP, C++
  - Focus on connection pooling, parameterized queries, and Redis caching

## Admin Interface (Lab 05)

Lab 05 introduces an admin interface framework for managing users, images, operations, and job queues. Students learn:
- Parsing database and cache URLs from environment variables
- Implementing connection pooling for efficient database access
- Writing parameterized SQL queries to prevent injection vulnerabilities
- Using Redis caching to reduce database load
- Handling database errors gracefully

The admin interface is available in three language flavors:
- **Python** ([admin/python/](admin/python/)) - Flask with psycopg2 and redis-py
- **PHP** ([admin/php/](admin/php/)) - Apache with PDO and phpredis
- **C++** ([admin/cpp/](admin/cpp/)) - Custom HTTP server with libpqxx and hiredis

Each implementation provides identical REST endpoints and web UI for consistency across languages.

## Additional Resources

- [PORTS.md](PORTS.md) - Student port assignments for Docker containers
- [DOCKERFILE_CHEATSHEET.md](DOCKERFILE_CHEATSHEET.md) - Dockerfile instructions reference
- [DOCKER_CHEATSHEET.md](DOCKER_CHEATSHEET.md) - Docker CLI command reference
- [DOCKER-COMPOSE.md](DOCKER-COMPOSE.md) - Docker Compose configuration guide
- [solutions/](solutions/) - Instructor reference implementations (restricted access)
- [Official Docker Documentation](https://docs.docker.com/)
- [Docker Hub](https://hub.docker.com/)
