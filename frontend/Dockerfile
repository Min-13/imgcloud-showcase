# Multi-stage Dockerfile for Python Flask Frontend
# Supports both LAB03 (basic) and LAB04 (with storage/database) functionality

# Stage 1: Build stage
FROM python:3.11-slim AS builder

# Install build dependencies for compiling Python packages
# LAB04: Added libpq-dev for PostgreSQL support
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file from frontend directory and proto file from imgprocessor directory
COPY frontend/requirements.txt .
COPY imgprocessor/image_processor.proto .

# Install dependencies to a local directory
RUN pip install --no-cache-dir --user -r requirements.txt

# Generate Python gRPC code from proto file
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. image_processor.proto

# Stage 2: Runtime stage
FROM python:3.11-slim

# LAB04: Install runtime dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /home/appuser/app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy generated gRPC code from builder
COPY --from=builder /app/image_processor_pb2.py .
COPY --from=builder /app/image_processor_pb2_grpc.py .

# Copy application code from frontend directory
COPY frontend/app.py .

# Copy static directory (needed for the root endpoint to serve index.html)
COPY static /home/appuser/static

# Change ownership to non-root user
RUN chown -R appuser:appuser /home/appuser

# Switch to non-root user
USER appuser

# Add .local/bin to PATH for installed packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose the port the app runs on
EXPOSE 8080

# Set environment variables (defaults for LAB03)
ENV PORT=8080
ENV PROCESSOR_HOST=imgprocessor
ENV PROCESSOR_HTTP_PORT=8080
ENV PROCESSOR_GRPC_PORT=50051

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the application
CMD ["python", "app.py"]
