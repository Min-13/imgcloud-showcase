# LAB03 - Background Information

This document provides background information about the technologies and architectural decisions used in LAB03.

## Why gRPC for Image Processing?

In a real-world production environment, gRPC offers several advantages over HTTP/REST for service-to-service communication:

1. **Performance**: Binary protocol (Protocol Buffers) is more efficient than JSON over HTTP
2. **Type Safety**: Strongly-typed contracts defined in `.proto` files prevent API mismatches
3. **Streaming**: Built-in support for streaming large binary data (like images) efficiently
4. **Code Generation**: Automatic client/server code generation from proto definitions
5. **HTTP/2**: Built on HTTP/2 for multiplexing and connection reuse

However, we keep HTTP for health checks because:
- Simple curl testing and monitoring tools expect HTTP
- No need for complex clients just to check if service is alive
- Standard practice in production Kubernetes environments

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User Browser                      │
│         http://csc.wils.one:30090                    │
│                (your assigned port)                  │
└────────────────────┬────────────────────────────────┘
                     │
                     │ HTTP (Web UI)
                     ▼
┌─────────────────────────────────────────────────────┐
│              Frontend Service (Python)               │
│            Public Port: 30090 → Internal: 8080       │
│  - Serves web UI                                     │
│  - Handles user requests                             │
│  - gRPC client to processor                          │
└────────────────────┬────────────────────────────────┘
                     │
                     │ gRPC (Port 50051)
                     │ Binary Protocol (Protobuf)
                     │ Internal Docker Network Only
                     ▼
┌─────────────────────────────────────────────────────┐
│         Image Processor Service (C++)                │
│          gRPC Port: 50051 (Internal Only)            │
│          HTTP Port: 8080 (Health - Internal Only)    │
│  - Performs image operations via gRPC                │
│  - resize, grayscale, blur, edge_detection           │
│  - rotate, mirror (NEW!)                             │
│  - HTTP health endpoint for monitoring               │
│  - NOT accessible from public internet               │
└─────────────────────────────────────────────────────┘
```

## Why Separate Services?

1. **Performance**: C++ is faster for computationally expensive image processing
2. **Scalability**: Services can be scaled independently (e.g., run multiple processor instances)
3. **Separation of Concerns**: Frontend handles UI/routing, processor handles computation
4. **Language-Specific Strengths**: Python for web, C++ for performance-critical operations
5. **Modern RPC**: gRPC provides efficient binary communication between services

## Comparison with Previous Labs

### LAB02 (Multi-Stage Build with Shared C++ Library)
- Single service with shared library
- Students could choose between Python or Go for their frontend
- C++ library linked at build time
- Library functions called directly (CGO for Go, ctypes for Python)

### LAB03 (Multi-Container Architecture with gRPC)
- Multiple services communicating over network
- **Frontend uses Python exclusively** (no language choice in this lab)
- C++ runs as separate service
- Communication via gRPC (binary protocol) for image processing
- HTTP maintained for health checks
- Services can be deployed and scaled independently
- More realistic production microservices pattern

## Key Learning Objectives

1. **Microservices Architecture**: Understand how to split an application into multiple services
2. **gRPC Communication**: Learn modern RPC framework for service-to-service communication
3. **Protocol Buffers**: Define service contracts with strongly-typed schemas
4. **Dual Protocols**: Understand when to use gRPC vs HTTP (processing vs health checks)
5. **Docker Compose**: Orchestrate multiple containers with dependencies
6. **Environment Variables**: Configure services for different environments
7. **Network Isolation**: Understand Docker networking and service discovery
8. **Multi-Stage Builds**: Apply multi-stage builds to multiple services
9. **Separation of Concerns**: Frontend for UI, backend for computation
10. **Production Patterns**: Learn real-world microservices best practices
