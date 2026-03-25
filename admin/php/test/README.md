# PHP Admin Module Tests

## Overview

Unit tests for the PHP admin interface implementation using PHPUnit, testing database connections, Redis caching, and all endpoints.

## Test Files

- `DatabaseTest.php` - Tests for database module (PDO, persistent connections, prepared statements)
- `CacheTest.php` - Tests for cache module (phpredis operations)
- `EndpointsTest.php` - Tests for all 5 endpoints (Users, Images, Operations, Jobs, Health)
- `phpunit.xml` - PHPUnit configuration
- `composer.json` - Dependencies

## Running Tests

### Install Dependencies

```bash
cd admin/php/test
composer install
```

### Run All Tests

```bash
vendor/bin/phpunit
```

### Run Specific Test File

```bash
vendor/bin/phpunit DatabaseTest.php
vendor/bin/phpunit CacheTest.php
vendor/bin/phpunit EndpointsTest.php
```

### With Coverage

```bash
vendor/bin/phpunit --coverage-html coverage/
```

## Test Categories

### Unit Tests
- Mock database and cache connections
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
- Singleton pattern
- PDO connection with persistent connections
- Prepared statement usage
- SQL injection prevention
- Connection pooling (PDO::ATTR_PERSISTENT)

### Cache Module
- URL parsing from REDIS_URL
- Singleton pattern
- Redis connection (phpredis)
- Set operation with TTL
- Get operation
- Delete operation
- JSON serialization

### Endpoints
- All 5 endpoint classes exist
- JSON response format
- Proper data structures
- Array key validation

## Comparing with Solutions

Tests are designed to validate student implementations against the working solutions in `solutions/lab05/php/`.

## PHPUnit Version

These tests are written for PHPUnit 9.5. For other versions, adjust `composer.json` accordingly.
