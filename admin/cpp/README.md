# Admin Interface - C++ Implementation

## Overview

This directory contains the C++ implementation of the LAB05 admin interface.

## Files to Complete

1. **db.h / db.cpp** - Database connection and query execution
2. **cache.h / cache.cpp** - Redis caching functionality
3. **endpoints.h / endpoints.cpp** - REST endpoint implementations with SQL queries

## Files Provided (Do Not Modify)

- **main.cpp** - HTTP server setup and routing
- **Dockerfile** - Container configuration
- **Makefile** - Build configuration
- **docker-compose.yml** - Service orchestration

## Instructions

See the main lab documentation:
- [LAB05.md](../../labs/lab05/LAB05.md) - Main lab instructions
- [LAB05-CPP.md](../../labs/lab05/LAB05-CPP.md) - C++-specific guide
- [LAB05-QUERIES.md](../../labs/lab05/LAB05-QUERIES.md) - SQL query requirements

## Quick Start

1. Complete the TODOs in `db.cpp`, `cache.cpp`, and `endpoints.cpp`
2. Add the admin service to your root `docker-compose.yml`
3. Run `docker compose up --build`
4. Access the UI at `http://localhost:YOUR_PORT`

## Building Locally

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt-get install libpqxx-dev libhiredis-dev nlohmann-json3-dev

# Build
make

# Run
./admin
```

## Testing

```bash
# Test endpoints
curl http://localhost:YOUR_PORT/api/users
curl http://localhost:YOUR_PORT/api/images
curl http://localhost:YOUR_PORT/api/operations
curl http://localhost:YOUR_PORT/api/jobs
curl http://localhost:YOUR_PORT/health
```

## Submission

Submit your completed:
- `db.cpp`
- `cache.cpp`
- `endpoints.cpp`
