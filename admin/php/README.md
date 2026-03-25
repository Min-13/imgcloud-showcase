# Admin Interface - PHP Implementation

## Overview

This directory contains the PHP implementation of the LAB05 admin interface.

## Files to Complete

1. **db.php** - Database connection and query execution
2. **cache.php** - Redis caching functionality
3. **endpoints.php** - REST endpoint implementations with SQL queries

## Files Provided (Do Not Modify)

- **index.php** - Application routing
- **Dockerfile** - Container configuration
- **docker-compose.yml** - Service orchestration

## Instructions

See the main lab documentation:
- [LAB05.md](../../labs/lab05/LAB05.md) - Main lab instructions
- [LAB05-PHP.md](../../labs/lab05/LAB05-PHP.md) - PHP-specific guide
- [LAB05-QUERIES.md](../../labs/lab05/LAB05-QUERIES.md) - SQL query requirements

## Quick Start

1. Complete the TODOs in `db.php`, `cache.php`, and `endpoints.php`
2. Add the admin service to your root `docker-compose.yml`
3. Run `docker compose up --build`
4. Access the UI at `http://localhost:YOUR_PORT`

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
- `db.php`
- `cache.php`
- `endpoints.php`
