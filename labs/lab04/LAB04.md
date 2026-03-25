# LAB04: Persistent Storage and State Management

## Overview

This lab extends the microservices architecture from LAB03 by adding persistent storage and state management capabilities:

1. **Frontend Service** (Python/Flask) - Enhanced with session management, user authentication, job tracking, and asynchronous processing
2. **Image Processor Service** (C++) - Same gRPC interface from LAB03 (no changes required)
3. **MinIO** - Object storage for images (per-student instance)
4. **Redis** - Session management, thumbnail caching, and job queue (per-student instance)
5. **PostgreSQL** - Shared database server with individual databases for each student

**Note:** The job queue functionality is implemented in the Python frontend for simplicity. The C++ processor remains unchanged from LAB03.

**Important:** The enhanced frontend/Dockerfile now includes support for all LAB04 features. The application will log the availability of each service (MinIO, Redis, PostgreSQL) and can operate with partial database setup, though full functionality requires all services to be properly configured.

**Supporting Documentation:**
- [LAB04-BACKGROUND.md](LAB04-BACKGROUND.md) - Architecture overview, design rationale, learning objectives
- [LAB04-STORAGE.md](LAB04-STORAGE.md) - MinIO object storage details
- [LAB04-DATABASE.md](LAB04-DATABASE.md) - PostgreSQL schema and usage
- [LAB04-CACHE.md](LAB04-CACHE.md) - Redis caching and session management
- [LAB04-ENVIRONMENT-VARIABLES.md](LAB04-ENVIRONMENT-VARIABLES.md) - Complete environment variable reference
- [LAB04-TESTING.md](LAB04-TESTING.md) - Comprehensive testing procedures
- [LAB04-TROUBLESHOOTING.md](LAB04-TROUBLESHOOTING.md) - Common problems and solutions

## Lab Requirements

### Shared vs. Per-Student Services

**Important:** This lab uses both shared and per-student services:

- **Shared PostgreSQL Server**: All students connect to the same PostgreSQL server, but each student has their own DATABASE on that server
- **Per-Student Services**: Each student runs their own MinIO and Redis instances in their docker-compose

### Your Tasks

For this lab, you need to **update your docker-compose.yml from LAB03** to add:
1. A MinIO service for object storage
2. A Redis service for caching and sessions
3. Environment variables to connect your frontend to all services
4. Configuration for the shared PostgreSQL database

**Starting Point:** You can use your own `docker-compose.yml` from LAB03, or compare it against the `docker-compose.lab03.yaml` file in the `labs/lab04/` directory, or use the lab03 version if you prefer. This contains a working LAB03 configuration.

**Important:** The enhanced `frontend/Dockerfile` now includes support for all LAB04 features (no separate Dockerfile needed). The image processor remains unchanged from LAB03.

**Before you begin**, review the provided Dockerfiles and understand the new dependencies added to support storage, caching, and database operations.

## Prerequisites

### Required Configuration

You will need:
- **PostgreSQL connection details** (host: `420s26-postgres` for Docker network access)
- **Your database name** (will match your STUDENTNAME, e.g., `alice`)
- **Your username and password** for database access
- **Your schema name** (will match your STUDENTNAME within your database)

**Port Assignment:** Refer to the `PORTS.md` file in the repository root for your assigned port range.

### Database Provisioning

**Important:** You need to provision your PostgreSQL database before starting this lab. You will receive:
1. A database name (matching your STUDENTNAME, e.g., `alice`)
2. A username (same as your STUDENTNAME)
3. A password for database access

**Provisioning Your Database:**

Connect to the shared PostgreSQL server using the provided credentials:

```bash
# Connect to PostgreSQL (you'll be prompted for your password)
docker exec -it 420s26-postgres psql -U STUDENTNAME -d STUDENTNAME
```

Once connected, create your schema and tables:

```sql
-- Create your schema
CREATE SCHEMA IF NOT EXISTS STUDENTNAME;

-- Set search path to your schema
SET search_path TO STUDENTNAME;

-- The tables will be created automatically by your application on first startup
-- Or you can create them manually if needed (see LAB04-DATABASE.md for table definitions)
```

**Connection String Format:**
```
postgresql://STUDENTNAME:PASSWORD@420s26-postgres:5432/STUDENTNAME
```

Your frontend application will automatically create the necessary tables in your schema on startup. Once you have your database credentials, update your docker-compose.yml with the connection details.

## Step-by-Step Docker Compose Setup

### Starting Point

You can use your own `docker-compose.yml` from LAB03, or refer to the `docker-compose.lab03.yaml` file in the `labs/lab04/` directory for reference. This contains a working LAB03 configuration with the frontend and image processor services already set up.

If starting fresh, you can copy the reference file:

```bash
cp labs/lab04/docker-compose.lab03.yaml docker-compose.yml
```

### Step 1: Add MinIO Object Storage

Add a MinIO service to your docker-compose.yml for object storage.

**What is MinIO?**
- S3-compatible object storage for images
- Replaces filesystem storage from previous labs
- Production-ready alternative to AWS S3

**Configuration requirements:**
- Use the official `minio/minio:latest` image
- Configure the MinIO server command to serve from a data directory
- Set up root credentials via environment variables (MINIO_ROOT_USER and MINIO_ROOT_PASSWORD)
- Create a named volume for persistent data storage
- Connect to your student network
- The MinIO service should NOT expose public ports (accessed through frontend only)

**Testing MinIO:**

```bash
# Start only MinIO
docker compose up STUDENTNAME-minio -d

# Check if it's running
docker compose ps

# Check the logs
docker compose logs STUDENTNAME-minio
```

**Expected behavior:**
- MinIO container starts successfully
- Logs show "MinIO Object Storage Server"
- No error messages in the logs

### Step 2: Add Redis Cache

Add a Redis service for session management and caching.

**What is Redis?**
- In-memory data store for fast access
- Used for session management (user login state)
- Used for thumbnail caching (faster image previews)
- Used for job queue (async processing)

**Configuration requirements:**
- Use the `redis:7-alpine` image
- Configure Redis to run with append-only file persistence
- Create a named volume for persistent data storage
- Connect to your student network
- The Redis service should NOT expose public ports (internal only)

**Testing Redis:**

```bash
# Start MinIO and Redis
docker compose up STUDENTNAME-minio STUDENTNAME-redis -d

# Check if they're running
docker compose ps

# Check the logs
docker compose logs STUDENTNAME-redis
```

**Expected behavior:**
- Redis container starts successfully
- Logs show "Ready to accept connections"
- No error messages in the logs

### Step 3: Verify Image Processor Service

The image processor service should already be configured from LAB03 - no changes needed.

**No changes from LAB03:**
- Same gRPC interface
- No Redis or MinIO dependencies
- Job queue managed by frontend

### Step 4: Update Frontend Service Configuration

Update your frontend service configuration to connect to all the new storage services.

**Required environment variables:**

See [LAB04-ENVIRONMENT-VARIABLES.md](LAB04-ENVIRONMENT-VARIABLES.md) for complete reference and examples.

**Summary of variables needed:**
- **MinIO**: `MINIO_HOST`, `MINIO_PORT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`
- **Redis**: `REDIS_HOST`, `REDIS_PORT`
- **PostgreSQL**: `DATABASE_URL` (full connection string), `DB_SCHEMA`
- **Processor** (from LAB03): `PROCESSOR_HOST`, `PROCESSOR_HTTP_PORT`, `PROCESSOR_GRPC_PORT`

**Important:** The DATABASE_URL format is:
```
postgresql://STUDENTNAME:PASSWORD@420s26-postgres:5432/STUDENTNAME
```

Replace `STUDENTNAME` with your actual username and `PASSWORD` with the password provided by your instructor.

### Step 5: Connect to Shared PostgreSQL Network

**Important:** Your frontend needs to connect to the shared PostgreSQL service, which runs on a shared Docker network.

**Discovering the shared network:**

Use the following command to list all Docker networks and find the shared network:

```bash
docker network ls
```

Look for a network that appears to be shared (it will have a name related to the class or PostgreSQL). Once you've identified it, you need to:

1. Add it as an external network in your docker-compose.yml
2. Connect your frontend service to both your own network AND the shared network

**Network configuration requirements:**
- Your frontend service must be on two networks: your own student network (for MinIO/Redis/processor communication) and the external shared network (for PostgreSQL access)
- The shared network should be configured as an `external: true` network in your docker-compose.yml
- Use the exact network name you discovered with `docker network ls`

**Why two networks?**
- Your personal network isolates your services (MinIO, Redis, processor) from other students
- The shared network provides access to the common PostgreSQL server

### Step 6: Test All Services Together

Start all services and verify they work together:

**Test commands:**

```bash
# Start all services
docker compose up --build -d

# Check all services are running
docker compose ps

# Test the health endpoint
curl http://localhost:YOUR_PORT/health

# View logs from all services
docker compose logs -f
```

**Expected behavior:**
- All containers start successfully
- Frontend health shows service availability status
- Frontend logs show which services are connected
- MinIO bucket is automatically created
- Redis accepts connections
- PostgreSQL schema is initialized

**Test in your browser:**

1. Navigate to `http://csc.wils.one:YOUR_PORT`
2. Register a new user account (stored in PostgreSQL)
3. Log in (session stored in Redis)
4. Upload an image (stored in MinIO)
5. Process the image (job queued in Redis, processed by imgprocessor)
6. View your image history (metadata from PostgreSQL, images from MinIO)
7. View thumbnail previews (cached in Redis)

**Success indicators:**
- ✅ Health check shows service availability
- ✅ User registration and login works
- ✅ Images upload to MinIO successfully
- ✅ Processing jobs complete
- ✅ Thumbnails load quickly (cached)
- ✅ Image history shows all uploads

**When done testing:**
```bash
docker compose down
```

### Key Configuration Checklist

Before submitting, verify your `docker-compose.yml` includes:
- ✅ Custom network with unique name (`STUDENTNAME-network`)
- ✅ All services connected to the same network
- ✅ Frontend has public port mapping (YOUR_PORT:8080) - check PORTS.md for your assigned port
- ✅ **MinIO service with named volume** for persistent storage (e.g., `STUDENTNAME-minio-data`)
- ✅ **Redis service with named volume** for persistent cache (e.g., `STUDENTNAME-redis-data`)
- ✅ Imgprocessor configured (same as LAB03, no changes needed)
- ✅ Frontend configured with environment variables for all storage services (see LAB04-ENVIRONMENT-VARIABLES.md)
- ✅ PostgreSQL connection string (format: `postgresql://STUDENTNAME:PASSWORD@420s26-postgres:5432/STUDENTNAME`)
- ✅ DB_SCHEMA set to STUDENTNAME (matches database and schema name)
- ✅ All service/container names prefixed with STUDENTNAME
- ✅ No public ports on internal services (MinIO, Redis, imgprocessor)

### Understanding Persistent Volumes

**Why Volumes Matter:**

Without volumes, all data is lost when containers are removed. For LAB04, you need persistent storage for:
- **MinIO**: Stores your uploaded images
- **Redis**: Stores sessions and cached thumbnails

**Volume Requirements:**

Each service that needs persistent storage must:
1. Have a **named volume** defined in the `volumes:` section at the bottom of your docker-compose.yml
2. Mount that volume to the correct path inside the container

Consult Docker Compose documentation for volume syntax and configuration. Name your volumes with your STUDENTNAME prefix (e.g., `STUDENTNAME-minio-data`, `STUDENTNAME-redis-data`).

**Volume Behavior:**
- `docker compose down` - Stops containers, **preserves** volume data
- `docker compose down -v` - Stops containers and **deletes** volume data (use carefully!)

**Checking your volumes:**
```bash
# List all volumes
docker volume ls

# Inspect a specific volume
docker volume inspect STUDENTNAME-minio-data
```

**Note:** PostgreSQL data persists on the shared server, not in your volumes. Only MinIO and Redis need volume configuration in your docker-compose.yml.

## Understanding Your Database

### Database vs. Schema

**Important Distinction:**
- The PostgreSQL server is shared among all students (running as Docker container `420s26-postgres`)
- You have your own **DATABASE** on this shared server (named after your STUDENTNAME, e.g., `alice`)
- Within your database, you have a **SCHEMA** also named after your STUDENTNAME (e.g., `alice`)
- All your tables are created as `STUDENTNAME.table_name` (e.g., `alice.users`, `alice.images`)

**Why both database AND schema?**

**Database-level isolation** provides:
- Complete data separation between students
- Independent backup/restore capability
- Separate connection limits and permissions
- Security boundary - you can't accidentally query another student's data

**Schema within database** provides:
- Namespace organization (could have multiple schemas for different purposes)
- Flexibility for future expansion (e.g., separate schemas for dev/test/prod)
- PostgreSQL best practice - explicit schema names prevent conflicts
- Consistent with SQLAlchemy's `search_path` configuration

**Practical example for student 'alice':**
- Database: `alice` (isolated from other students' databases)
- Schema: `alice` (organizes tables within the database)
- Tables: `alice.users`, `alice.images`, `alice.jobs`
- Connection: `postgresql://alice:password@420s26-postgres:5432/alice`
- In SQLAlchemy: `search_path=alice` ensures all queries target your schema

This dual-level isolation is common in multi-tenant PostgreSQL deployments and teaches you production database architecture patterns.
- Tables: `alice.users`, `alice.images`, `alice.jobs`

### Database Tables

Your PostgreSQL database will include these tables (automatically created by the frontend application):

- **users**: User accounts with authentication credentials
- **images**: Image metadata and MinIO storage references
- **jobs**: Processing job queue and status tracking

**Note:** The schema and tables will be automatically created by your frontend service on first startup using SQLAlchemy migrations. You only need to use the connection details provided by your instructor.

## Building and Running with Docker Compose

### Start All Services

```bash
# Start in detached mode (background)
docker compose up --build -d

# Or start with logs visible (foreground)
docker compose up --build
```

### Access Your Application

Once running, access your application:
- **Web UI**: `http://csc.wils.one:YOUR_PORT`
- **Health Check**: `curl http://localhost:YOUR_PORT/health`

### View Logs

```bash
# View logs from all services
docker compose logs

# View logs from a specific service
docker compose logs STUDENTNAME-frontend

# Follow logs in real-time
docker compose logs -f
```

### Stop All Services

```bash
docker compose down
```

This stops and removes the containers but keeps the volumes (your data persists).

## Testing Your Implementation

For comprehensive testing procedures, see [LAB04-TESTING.md](LAB04-TESTING.md).

**Quick verification:**
1. Check all services are running: `docker compose ps`
2. Test health endpoint: `curl http://localhost:YOUR_PORT/health`
3. Register and login a test user
4. Upload and process an image
5. Verify data persists after restarting services

## Cleanup

```bash
# Stop and remove containers and networks
docker compose down

# Remove volumes (WARNING: deletes all your data)
docker compose down -v
```

**Important Cleanup Rules**:
- Always run `docker compose down` when finished with testing
- Use `docker compose down -v` only if you want to delete all data
- Your MinIO and Redis data is stored in Docker volumes
- PostgreSQL data is shared and persists on the server

## Submission

When submitting your lab:

1. Create and include your `docker-compose.yml` in your repository
2. Tag your final submission:
   ```bash
   git add docker-compose.yml
   git commit -m "Complete Lab04"
   git tag lab04-final
   git push origin main --tags
   ```

Your submission should include only:
- `docker-compose.yml` - Your orchestration file for all services

**Note:** The updated `frontend/Dockerfile` and `frontend/app.py` are provided for you.

## Summary

This lab demonstrates a production-ready microservices architecture with:
- **Object Storage (MinIO)**: S3-compatible storage for images, replacing filesystem storage
- **Relational Database (PostgreSQL)**: Structured data for users, images, and jobs with individual databases per student
- **Cache/Queue (Redis)**: Fast session management, thumbnail caching, and job queuing
- **Service Orchestration**: All services communicate via Docker network
- **Data Persistence**: Volumes preserve data across container restarts
- **Shared Resources**: PostgreSQL server shared across all students for realistic multi-tenant setup
- **Isolated Resources**: Each student has their own database, MinIO instance, and Redis instance for data isolation

For a deeper understanding of these concepts, see [LAB04-BACKGROUND.md](LAB04-BACKGROUND.md).
