# Admin Interface - LAB05

This directory contains three implementations of the admin interface for LAB05. Students choose **one** implementation to work with.

## Directory Structure

```
admin/
├── static/
│   └── admin.html          # Shared web UI for all implementations
├── python/                 # Python implementation
│   ├── db.py              # Students complete: database module
│   ├── cache.py           # Students complete: cache module
│   ├── endpoints.py       # Students complete: endpoint queries
│   ├── app.py             # Provided: Flask routing
│   ├── Dockerfile         # Provided: multi-stage build
│   └── requirements.txt   # Provided: dependencies
├── php/                    # PHP implementation
│   ├── db.php             # Students complete: database module
│   ├── cache.php          # Students complete: cache module
│   ├── endpoints.php      # Students complete: endpoint queries
│   ├── index.php          # Provided: routing
│   └── Dockerfile         # Provided: multi-stage build
└── cpp/                    # C++ implementation
    ├── db.h/cpp           # Students complete: database module
    ├── cache.h/cpp        # Students complete: cache module
    ├── endpoints.h/cpp    # Students complete: endpoint queries
    ├── main.cpp           # Provided: HTTP server
    ├── Dockerfile         # Provided: multi-stage build
    └── Makefile           # Provided: build configuration
```

## What Students Implement

Students complete **three files** in their chosen language:

1. **Database Module** - URL parsing, connection pooling, parameterized queries
2. **Cache Module** - URL parsing, Redis operations (get/set/delete)
3. **Endpoints Module** - SQL queries for users, images, operations, and jobs

## What Is Provided

The framework provides:
- Complete HTTP server / routing (no changes needed)
- Shared HTML UI with four tabs
- Docker configuration and build setup
- Endpoint structure with TODOs

## Key Learning Objectives

- Parse connection URLs from environment variables
- Implement connection pooling
- Write parameterized SQL queries (prevent SQL injection)
- Implement Redis caching with TTL
- Handle database errors gracefully

## Integration

Students add the admin service to their root-level `docker-compose.yml`:

```yaml
services:
  admin:
    build: ./admin/python  # or ./admin/php or ./admin/cpp
    ports:
      - "YOUR_PORT:8090"  # Use assigned port range
    environment:
      DATABASE_URL: postgresql://user:pass@420s26-postgres:5432/yourdb
      REDIS_URL: redis://redis:6379
      ADMIN_PORT: 8090
      CACHE_TTL: 300
    depends_on:
      - redis
    networks:
      - imgcloud
```

## Documentation

- [LAB05.md](../labs/lab05/LAB05.md) - Main lab instructions
- [LAB05-PYTHON.md](../labs/lab05/LAB05-PYTHON.md) - Python guide
- [LAB05-PHP.md](../labs/lab05/LAB05-PHP.md) - PHP guide
- [LAB05-CPP.md](../labs/lab05/LAB05-CPP.md) - C++ guide
- [LAB05-QUERIES.md](../labs/lab05/LAB05-QUERIES.md) - SQL query requirements

## Solutions

Complete working solutions are available in `solutions/lab05/` for instructor reference.
