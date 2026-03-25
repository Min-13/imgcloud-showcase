# Lab04 Starting Point for Lab06

This directory provides the **lab04 docker-compose solution** as a fresh starting base for students beginning Lab06.

## Using This as Your Starting Point

If you do not have a working Lab04 setup, copy the reference docker-compose to your repository root:

```bash
cp labs/lab06/docker-compose-lab04.yml docker-compose.yml
```

Then edit `docker-compose.yml` and replace every instance of `STUDENTNAME` with your actual username and fill in your port from `PORTS.md`.

## What the Lab04 Solution Includes

`docker-compose-lab04.yml` configures the full Lab04 stack:

- **imgprocessor** - C++ image processing service (gRPC + HTTP)
- **frontend** - Python/Flask web UI connected to imgprocessor, MinIO, Redis, and PostgreSQL
- **minio** - Per-student S3-compatible object storage for images
- **redis** - Per-student Redis for sessions, thumbnail cache, and job queue

The frontend connects to the **shared PostgreSQL server** via the `420s26-shared-services` external network.

## Files Needed for Lab06 CI

Once you have a working Lab04 base, Lab06 asks you to add CI for the **frontend tests** that already exist in the repository:

- `frontend/test_empty_params.py`
- `frontend/test_form_submission.py`

These tests verify the frontend application logic and do not require a running database, MinIO, or Redis.
