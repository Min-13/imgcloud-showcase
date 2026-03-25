# Admin Interface - Python Implementation

## Overview

This directory contains the Python implementation of the LAB05 admin interface.

## Files to Complete

1. **db.py** - Database connection and query execution
2. **cache.py** - Redis caching functionality
3. **endpoints.py** - REST endpoint implementations with SQL queries

## Files Provided (Do Not Modify)

- **app.py** - Flask application setup and routing
- **Dockerfile** - Container configuration
- **docker-compose.yml** - Service orchestration
- **requirements.txt** - Python dependencies

## Instructions

See the main lab documentation:
- [LAB05.md](../../labs/lab05/LAB05.md) - Main lab instructions
- [LAB05-PYTHON.md](../../labs/lab05/LAB05-PYTHON.md) - Python-specific guide
- [LAB05-QUERIES.md](../../labs/lab05/LAB05-QUERIES.md) - SQL query requirements

## Quick Start

1. Complete the TODOs in `db.py`, `cache.py`, and `endpoints.py`
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
- `db.py`
- `cache.py`
- `endpoints.py`
