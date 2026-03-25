# Multi-stage Dockerfile for C++ Image Processor with gRPC
# This demonstrates building a C++ service with OpenCV and gRPC

# Stage 1: Build stage
FROM ubuntu:22.04 AS builder

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies including gRPC and protobuf
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    pkg-config \
    libopencv-dev \
    libgrpc++-dev \
    libprotobuf-dev \
    protobuf-compiler-grpc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy source code and proto file
COPY imgprocessor/*.cpp ./
COPY imgprocessor/*.h ./
COPY imgprocessor/*.proto ./
COPY imgprocessor/Makefile ./

# Build the application
RUN make

# Stage 2: Runtime stage
FROM ubuntu:22.04

# Install runtime dependencies for OpenCV and gRPC
# Using minimal runtime libraries to keep image size small
RUN apt-get update && apt-get install -y \
    libopencv-core4.5d \
    libopencv-imgcodecs4.5d \
    libopencv-imgproc4.5d \
    libgrpc++1 \
    libprotobuf23 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /home/appuser

# Copy the compiled binary from builder
COPY --from=builder /build/imgprocessor .

# Change ownership to non-root user
RUN chown -R appuser:appuser /home/appuser

# Switch to non-root user
USER appuser

# Expose the ports the service runs on
# 8080: HTTP health check endpoint
# 50051: gRPC service endpoint
EXPOSE 8080 50051

# Set environment variables
ENV HTTP_PORT=8080
ENV GRPC_PORT=50051

# Run the application
CMD ["./imgprocessor"]
