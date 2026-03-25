# LAB05: Database Connections and Caching

## Learning Objectives

By completing this assignment, you will:

- Configure database connections using environment variables
- Implement connection pooling for efficient database access
- Write parameterized SQL queries to prevent injection vulnerabilities
- Implement Redis caching to reduce database load
- Handle database errors gracefully
- Integrate database operations with a web application

## Requirements

You will implement an admin interface that displays information about users, images, operations performed, and job queue status. The framework (HTTP server, routing, UI) is provided. You need to complete:

1. **Database connection module** - URL parsing, connection pooling, query execution
2. **Redis cache module** - URL parsing, get/set/delete operations
3. **Endpoint implementations** - Write SQL queries AND implement caching logic for Users and Images endpoints

## Getting Started

### 1. Choose Your Language

Navigate to one of:
- `admin/python/` - Flask, psycopg2, redis-py ([LAB05-PYTHON.md](LAB05-PYTHON.md))
- `admin/php/` - PDO, phpredis ([LAB05-PHP.md](LAB05-PHP.md))
- `admin/cpp/` - libpqxx, hiredis ([LAB05-CPP.md](LAB05-CPP.md))

All three implementations provide the same functionality and REST endpoints.

### 2. Review Provided Code

The framework includes:
- **HTTP server and routing** - Handles requests and responses (provided)
- **Operations and Jobs endpoints** - Two complete endpoint implementations as examples (provided)
- **HTML UI** - Admin interface (`admin/static/admin.html`, provided)

You need to complete:
- **Database module** (`db.*`) - Connection pool warmup
- **Cache module** (`cache.*`) - Redis database selection
- **Endpoints module** (`endpoints.*`) - SQL queries for Users and Images

### 3. Implement Database Module

**What's Provided:**
- URL parsing from `DATABASE_URL` environment variable
- Connection pool creation and configuration
- Query execution methods

**What You Must Implement:**
- **Connection pool warmup** - Pre-create 3 initial connections to warm up the pool and test connectivity
- This ensures the pool is ready before handling requests

Look for the TODO in your language's `db.*` file that indicates where to implement this.

### 4. Implement Cache Module

**What's Provided:**
- URL parsing from `REDIS_URL` environment variable
- Redis connection setup
- Full implementation of get, set (with TTL), and delete operations

**What You Must Implement:**
- **Redis database selection** - Parse the database number from `REDIS_URL` (e.g., `redis://host:port/2`) and execute the Redis `SELECT` command to select the appropriate database
- Handle reply cleanup properly (especially important in C++)

Look for the TODO in your language's `cache.*` file that indicates where to implement this. The Redis command you need is:
```
SELECT <database_number>
```

### 5. Implement Endpoints with Caching

Implement two endpoints following the caching pattern from the provided examples:
- **Users endpoint** - List users with image and job counts
- **Images endpoint** - Recent 100 images with user info

**Required implementation for each endpoint:**
1. **Check cache first** - Use appropriate cache key (`admin:users` or `admin:images`)
2. **Query database if cache miss** - Execute SQL query (see [LAB05-QUERIES.md](LAB05-QUERIES.md))
3. **Format response** - Include data, `cached` flag, and `cache_ttl`
4. **Store result in cache** - Use TTL of 300 seconds
5. **Return JSON response**

Study the provided Operations and Jobs endpoints to see this pattern in action. Your Users and Images endpoints must follow the exact same caching strategy.

### 6. Configure Docker

Add the admin service to your root `docker-compose.yml`:

```yaml
services:
  admin:
    build:
      context: ./admin
      dockerfile: python/Dockerfile  # or php/Dockerfile or cpp/Dockerfile
    ports:
      - "YOUR_PORT:8090"  # Use port from your assigned range
    environment:
      DATABASE_URL: postgresql://USERNAME:PASSWORD@postgres:5432/USERNAME
      REDIS_URL: redis://redis:6379
      ADMIN_PORT: 8090
      CACHE_TTL: 300
    depends_on:
      - redis
    networks:
      - USERNAME-network         # Your internal network
      - 420s26-shared-services   # For PostgreSQL access
```

**Important:** 
- Use a port from your assigned range ([PORTS.md](../../PORTS.md))
- Replace `USERNAME` with your actual username
- Replace `PASSWORD` with your database password
- Connect to both your internal network (`USERNAME-network`) and `420s26-shared-services` for database access
- Your Redis instance should be on your `USERNAME-network`

## REST Endpoints

Your admin interface provides:

- `GET /api/users` - Users with statistics (YOU IMPLEMENT)
- `GET /api/images` - Recent images (YOU IMPLEMENT)
- `GET /api/operations` - Operation statistics (PROVIDED)
- `GET /api/jobs` - Job queue status (PROVIDED)
- `GET /health` - Health check (PROVIDED)

Response format includes cache status:
```json
{
  "users": [...],
  "cached": true,
  "cache_ttl": 300
}
```

## Understanding the Expected JSON Format

**IMPORTANT:** The admin UI (`admin/static/admin.html`) expects specific field names in your JSON responses. Using incorrect field names will cause "undefined" to appear in the UI.

### How to Determine Expected Fields

**Method 1: Examine the HTML Code**

Open `admin/static/admin.html` and search for where each endpoint's data is used:

1. Search for `data.operations.forEach` to see Operations fields (around line 411)
2. Search for `data.jobs.forEach` to see Jobs fields (around line 462)
3. Search for `data.queue_stats` to see queue statistics fields (around line 446)
4. Search for `data.users.forEach` to see Users fields (around line 331)
5. Search for `data.images.forEach` to see Images fields (around line 370)

**Method 2: Use the Reference Below**

### Required JSON Structure

**Operations Endpoint (`/api/operations`):**
```json
{
  "operations": [
    {
      "operation": "resize",           // Operation name (string)
      "count": 100,                    // Total operations (int) - NOT "total"
      "completed_count": 95,           // Completed (int) - NOT "completed"
      "failed_count": 5,               // Failed (int) - NOT "failed"
      "avg_time_ms": 123.45           // Average time in ms (float)
    }
  ],
  "cached": false,
  "cache_ttl": 300
}
```

**Jobs Endpoint (`/api/jobs`):**
```json
{
  "jobs": [
    {
      "id": 1,                         // Job ID (int)
      "username": "user1",             // Username (string)
      "operation": "resize",           // Operation type (string)
      "status": "completed",           // Status (string)
      "created_at": "2024-01-01T12:00:00",  // ISO timestamp (string)
      "completed_at": "2024-01-01T12:05:00" // ISO timestamp or null (string/null)
    }
  ],
  "queue_stats": {
    "pending": 5,                      // Count (int)
    "processing": 2,                   // Count (int)
    "completed": 100,                  // Count (int)
    "failed": 3                        // Count (int)
  },
  "cached": false,
  "cache_ttl": 60
}
```

**Users Endpoint (`/api/users`):**
```json
{
  "users": [
    {
      "id": 1,                         // User ID (int)
      "username": "user1",             // Username (string)
      "email": "user@example.com",     // Email (string)
      "created_at": "2024-01-01T12:00:00", // ISO timestamp (string)
      "image_count": 10,               // Image count (int)
      "job_count": 5                   // Job count (int)
    }
  ],
  "cached": false,
  "cache_ttl": 300
}
```

**Images Endpoint (`/api/images`):**
```json
{
  "images": [
    {
      "id": 1,                         // Image ID (int)
      "user_id": 1,                    // User ID (int)
      "username": "user1",             // Username (string)
      "original_filename": "photo.jpg", // Original filename (string) - matches DB column
      "file_size": 102400,             // Size in bytes (int) - matches DB column
      "content_type": "image/jpeg",    // MIME type (string)
      "upload_date": "2024-01-01T12:00:00"  // ISO timestamp (string) - matches DB column
    }
  ],
  "total": 100,                        // Total count (int)
  "cached": false,
  "cache_ttl": 300
}
```
⚠️ **Important**: Use exact database column names: `original_filename`, `file_size`, `upload_date` (NOT `filename`, `size`, `uploaded_at`)

**Common Mistakes:**
- ❌ Using `"total"` instead of `"count"` in Operations
- ❌ Using `"completed"` instead of `"completed_count"` in Operations
- ❌ Using `"failed"` instead of `"failed_count"` in Operations
- ❌ Returning non-ISO date strings (use `.isoformat()` in Python, `toISOString()` in JS)
- ❌ Missing the `queue_stats` object in Jobs response
- ❌ Wrong data types (strings instead of ints, or vice versa)

**Testing Your JSON:**
```bash
# Test your endpoint and check field names
curl http://localhost:YOUR_PORT/api/operations | jq .

# Verify no "undefined" appears in the UI browser console
```

## Testing

### Important: Data Migration Warning

**⚠️ CRITICAL: Backup MinIO Data Before Running Lab05**

If you're adding the admin service to an existing docker-compose.yml that includes MinIO storage:

1. **Back up your MinIO data first:**
   ```bash
   # Stop services
   docker-compose down
   
   # Backup MinIO volume
   docker run --rm -v yourproject_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio-backup.tar.gz /data
   ```

2. **Why this matters:**
   - Adding new services can sometimes cause Docker to recreate volumes
   - If PostgreSQL/Redis volumes are recreated while MinIO is running, data loss can occur
   - Always backup before making infrastructure changes

3. **Restore if needed:**
   ```bash
   # If you lose MinIO data, restore from backup:
   docker run --rm -v yourproject_minio_data:/data -v $(pwd):/backup alpine tar xzf /backup/minio-backup.tar.gz -C /
   ```

4. **Best practice:**
   - Use explicit volume names in docker-compose.yml
   - Keep backups of all volumes regularly
   - Test on a copy of your docker-compose.yml first

### Running the Admin Service

1. Build and start the service:
```bash
docker-compose up --build admin
```

2. Access the HTML UI:
```
http://localhost:YOUR_PORT/
```

3. Test endpoints:
```bash
curl http://localhost:YOUR_PORT/health
curl http://localhost:YOUR_PORT/api/users
curl http://localhost:YOUR_PORT/api/images
curl http://localhost:YOUR_PORT/api/operations
curl http://localhost:YOUR_PORT/api/jobs
```

## Submission

Submit your completed files:
- Database module (`db.py`, `db.php`, or `db.cpp`)
- Cache module (`cache.py`, `cache.php`, or `cache.cpp`)
- Endpoints module (`endpoints.py`, `endpoints.php`, or `endpoints.cpp`)
- Updated `docker-compose.yml`

Include screenshots showing:
1. Working HTML UI with data loaded
2. Successful API responses from all endpoints

## Additional Resources

- [LAB05-QUERIES.md](LAB05-QUERIES.md) - SQL query requirements and caching pattern
- [LAB05-REDIS.md](LAB05-REDIS.md) - Redis caching guide and testing
- [LAB05-REGEX.md](LAB05-REGEX.md) - Regular expressions for URL parsing
- [LAB05-TROUBLESHOOTING.md](LAB05-TROUBLESHOOTING.md) - Debugging guide
- Language-specific guides:
  - [LAB05-PYTHON.md](LAB05-PYTHON.md) - Safe parameter binding with psycopg2
  - [LAB05-PHP.md](LAB05-PHP.md) - Safe parameter binding with PDO
  - [LAB05-CPP.md](LAB05-CPP.md) - Safe parameter binding with libpqxx
