# Python Admin Module Tests

## Overview

Unit tests for the Python admin interface implementation, testing database connections, Redis caching, and all endpoints.

## Test Files

- `test_db.py` - Tests for database module (connection pooling, parameterized queries)
- `test_cache.py` - Tests for cache module (Redis operations)
- `test_endpoints.py` - Tests for all 5 endpoints (Users, Images, Operations, Jobs, Health)
- `run_tests.py` - Test runner script

## Running Tests

### Install Dependencies

```bash
cd admin/python/test
pip install -r requirements.txt
```

### Run All Tests

Using unittest:
```bash
python run_tests.py
```

Using pytest:
```bash
pytest -v
```

### Run Specific Test File

```bash
python -m unittest test_db.py
python -m unittest test_cache.py
python -m unittest test_endpoints.py
```

### With Coverage

```bash
pytest --cov=../ --cov-report=html
```

## Test Categories

### Unit Tests
- Mock database and cache connections
- Test individual functions and methods
- Validate input/output formats

### Integration Tests
- Require test database (set `TEST_DATABASE_URL` environment variable)
- Require test Redis (set `TEST_REDIS_URL` environment variable)
- Test real connections and operations

## Environment Variables

For integration tests, set:
```bash
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"
export TEST_REDIS_URL="redis://localhost:6379/1"
```

## What's Tested

### Database Module
- URL parsing from DATABASE_URL
- Connection pool creation (ThreadedConnectionPool)
- Parameterized query execution
- SQL injection prevention
- Thread safety

### Cache Module
- URL parsing from REDIS_URL
- Redis connection
- Set operation with TTL
- Get operation
- Delete operation
- JSON serialization
- Thread safety

### Endpoints
- All 5 endpoint classes exist
- JSON response format
- Cache hit/miss behavior
- Proper data structures
- Error handling

## Comparing with Solutions

Tests are designed to validate student implementations against the working solutions in `solutions/lab05/python/`.
