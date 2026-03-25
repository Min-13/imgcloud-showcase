# C++ Admin Module Tests

## Overview

Unit tests for the C++ admin interface implementation using Google Test, testing database connections, Redis caching, and all endpoints.

## Test Files

- `test_db.cpp` - Tests for database module (connection pool, libpqxx)
- `test_cache.cpp` - Tests for cache module (hiredis operations)
- `test_endpoints.cpp` - Tests for all 5 endpoints (Users, Images, Operations, Jobs, Health)
- `Makefile` - Build configuration

## Running Tests

### Install Dependencies

On Ubuntu/Debian:
```bash
sudo apt-get install libgtest-dev libgmock-dev
```

### Build Tests

```bash
cd admin/cpp/test
make
```

### Run All Tests

```bash
make test
```

### Run Specific Test

```bash
./test_db
./test_cache
./test_endpoints
```

## Test Categories

### Unit Tests
- Mock connections where possible
- Test individual functions and methods
- Validate input/output formats

### Integration Tests
- Require test database (set `DATABASE_URL` environment variable)
- Require test Redis (set `REDIS_URL` environment variable)
- Test real connections and operations

## Environment Variables

For integration tests, set:
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"
export REDIS_URL="redis://localhost:6379/1"
```

## What's Tested

### Database Module
- URL parsing from DATABASE_URL
- Manual connection pool creation (std::vector<unique_ptr<connection>>)
- Connection pool thread safety with mutex
- Maximum connections limit (10)
- Parameterized query execution (exec_params with $1, $2, etc.)
- SQL injection prevention

### Cache Module
- URL parsing from REDIS_URL
- Redis connection (hiredis)
- Set operation with TTL
- Get operation returning optional<json>
- Delete operation
- JSON serialization/deserialization
- Thread safety

### Endpoints
- All 5 endpoint classes exist and inherit from Endpoint base class
- handleRequest() method returns valid JSON string
- Proper response structures:
  - Users: `{"users": [...], "cached": bool, "cache_ttl": int}`
  - Images: `{"images": [...], "cached": bool, "cache_ttl": int}`
  - Operations: `{"operations": [...], "cached": bool, "cache_ttl": int}`
  - Jobs: `{"jobs": [...], "queue_stats": {...}, "cached": bool}`
  - Health: `{"status": "healthy|unhealthy", "database": bool, "cache": bool}`
- Caching behavior (cache check → DB query → cache store)

## Comparing with Solutions

Tests are designed to validate student implementations against the working solutions in `solutions/lab05/cpp/`.

## Google Test Framework

These tests use Google Test (gtest) and Google Mock (gmock) frameworks. Make sure they are installed on your system.

## Compilation

Tests are compiled with C++17 standard and link against:
- libpqxx (PostgreSQL C++ library)
- libhiredis (Redis C library)
- libgtest (Google Test)
- pthread (threading support)
