# Multi-stage build for C++ admin interface
FROM ubuntu:22.04 as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    libpq-dev \
    libpqxx-dev \
    libhiredis-dev \
    nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source files
COPY cpp/Makefile .
COPY cpp/*.cpp .
COPY cpp/*.h .

# Build application
RUN make

# Final stage - runtime only
FROM ubuntu:22.04

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    libpqxx-6.4 \
    libhiredis0.14 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy compiled binary from builder
COPY --from=builder /app/admin .

# Copy static files
COPY static ./static

# Expose port
EXPOSE 8090

# Run the application
CMD ["./admin"]
