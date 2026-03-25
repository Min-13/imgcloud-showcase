# LAB05 Testing Guide

## Overview

Comprehensive unit tests have been created for all three language implementations (Python, PHP, C++) of the admin interface. These tests validate student implementations against working solutions.

## Test Structure

```
admin/
├── python/test/
│   ├── test_db.py           # Database module tests
│   ├── test_cache.py        # Cache module tests
│   ├── test_endpoints.py    # Endpoints tests
│   ├── run_tests.py         # Test runner
│   ├── requirements.txt     # Test dependencies
│   └── README.md           # Python testing docs
├── php/test/
│   ├── DatabaseTest.php     # Database module tests
│   ├── CacheTest.php        # Cache module tests
│   ├── EndpointsTest.php    # Endpoints tests
│   ├── phpunit.xml         # PHPUnit config
│   ├── composer.json       # Dependencies
│   └── README.md           # PHP testing docs
└── cpp/test/
    ├── test_db.cpp          # Database module tests
    ├── test_cache.cpp       # Cache module tests
    ├── test_endpoints.cpp   # Endpoints tests
    ├── Makefile            # Build config
    └── README.md           # C++ testing docs
```

## What's Tested

### Database Module
- ✅ DATABASE_URL parsing
- ✅ Connection pool creation
- ✅ Parameterized queries
- ✅ SQL injection prevention
- ✅ Thread safety
- ✅ Singleton pattern (PHP)
- ✅ Persistent connections (PHP)

### Cache Module
- ✅ REDIS_URL parsing
- ✅ Redis connection
- ✅ Set operation with TTL
- ✅ Get operation
- ✅ Delete operation
- ✅ Cache miss handling
- ✅ JSON serialization
- ✅ Thread safety
- ✅ Singleton pattern (PHP)

### Endpoints
- ✅ All 5 endpoint classes exist
- ✅ Users endpoint (cache hit/miss, proper structure)
- ✅ Images endpoint (cache hit/miss, proper structure)
- ✅ Operations endpoint (statistics, timing)
- ✅ Jobs endpoint (jobs list + queue stats)
- ✅ Health endpoint (database + cache status)
- ✅ JSON response format validation
- ✅ Caching behavior

## Running Tests

### Python
```bash
cd admin/python/test
pip install -r requirements.txt
pytest -v                    # Run all tests
pytest --cov=../ --cov-report=html  # With coverage
```

### PHP
```bash
cd admin/php/test
composer install
vendor/bin/phpunit           # Run all tests
vendor/bin/phpunit --coverage-html coverage/  # With coverage
```

### C++
```bash
cd admin/cpp/test
make                         # Build tests
make test                    # Run all tests
./test_db                    # Run specific test
```

## Test Types

### Unit Tests
- Mock database and cache connections
- Test individual functions
- Validate input/output formats
- No external dependencies required

### Integration Tests
- Test with real database and Redis
- Set environment variables:
  ```bash
  export TEST_DATABASE_URL="postgresql://user:pass@host:5432/testdb"
  export TEST_REDIS_URL="redis://host:6379/1"
  ```
- Skipped if environment not configured

## Validation Against Solutions

Tests are designed to ensure student implementations match the behavior of working solutions in `solutions/lab05/{language}/`:

1. **Structural Validation**: Correct classes, methods, signatures
2. **Behavioral Validation**: Same inputs produce same outputs
3. **Format Validation**: JSON structures match specifications
4. **Security Validation**: SQL injection prevention, parameter binding

## Testing Best Practices

### For Students
1. Run tests frequently during development
2. Start with unit tests (no database required)
3. Use tests to understand expected behavior
4. Fix tests one by one, not all at once

### For Instructors
1. Copy solution files to admin/ directory
2. Run tests to verify solutions work
3. Use tests to grade student submissions
4. Add custom tests for specific requirements

## Test Frameworks

- **Python**: unittest + pytest
- **PHP**: PHPUnit 9.5
- **C++**: Google Test + Google Mock

## Coverage Goals

Aim for:
- 80%+ code coverage on db and cache modules
- 70%+ code coverage on endpoints module
- 100% class/method existence

## Common Issues

### Python
- Import errors: Ensure parent directory in sys.path
- Mock issues: Use `patch` decorator correctly
- Async issues: Not applicable (synchronous code)

### PHP
- Autoloading: Use composer autoload or require_once
- Singleton testing: Use reflection to reset instances
- Extension missing: Install php-redis

### C++
- Linking errors: Ensure all libraries linked (-lpqxx -lhiredis -lgtest)
- Header not found: Check include paths (-I..)
- GTest not installed: `sudo apt-get install libgtest-dev`

## Next Steps

1. Run tests on student submissions
2. Generate coverage reports
3. Identify common failures
4. Update documentation based on findings
5. Add more edge case tests as needed

## See Also

- `admin/python/test/README.md` - Python-specific testing guide
- `admin/php/test/README.md` - PHP-specific testing guide
- `admin/cpp/test/README.md` - C++-specific testing guide
- `labs/lab05/LAB05.md` - Main assignment
- `solutions/lab05/README.md` - Solution documentation
