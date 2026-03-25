# LAB04 - Background Information

This document provides background information about the storage, database, and caching technologies used in LAB04.

## Why Add Persistent Storage and State Management?

In real-world production environments, applications need to:

1. **Persist data across restarts** - Data must survive container crashes or updates
2. **Store large files efficiently** - Object storage is optimized for binary data like images
3. **Manage user state** - Sessions and authentication require server-side storage
4. **Cache frequently accessed data** - Reduce database load and improve performance
5. **Queue asynchronous tasks** - Process jobs in the background without blocking users
6. **Store structured data** - Relational databases for complex queries and relationships

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User Browser                      │
│         http://csc.wils.one:30090                    │
└────────────────────┬────────────────────────────────┘
                     │
                     │ HTTP (Web UI + REST API)
                     ▼
┌─────────────────────────────────────────────────────┐
│              Frontend Service (Python)               │
│            Public Port: 30090 → Internal: 8080       │
│  - Serves web UI and REST API                        │
│  - Manages user sessions (Redis)                     │
│  - Stores images (MinIO)                             │
│  - Queries metadata (PostgreSQL)                     │
│  - Queues jobs (Redis)                               │
│  - gRPC client to processor                          │
└───┬──────────┬──────────┬──────────┬────────────────┘
    │          │          │          │
    │          │          │          │ gRPC (Port 50051)
    │          │          │          │
    │          │          │          ▼
    │          │          │     ┌─────────────────────────┐
    │          │          │     │  Image Processor (C++)   │
    │          │          │     │   - Processes images     │
    │          │          │     │   - Reads from job queue │
    │          │          │     │   - Writes results back  │
    │          │          │     └─────────────────────────┘
    │          │          │          │
    │          │          │          │ Redis (Queue)
    │          │          │          │
    │          │          │     ┌────▼────────────────────┐
    │          │          │     │   Redis (Per-Student)   │
    │          │          └─────┤   - Session storage     │
    │          │                │   - Thumbnail cache     │
    │          │                │   - Job queue           │
    │          │                └─────────────────────────┘
    │          │
    │          │ S3 API (Port 9000)
    │          │
    │          │     ┌─────────────────────────┐
    │          └─────┤  MinIO (Per-Student)    │
    │                │   - Original images     │
    │                │   - Processed results   │
    │                │   - S3-compatible API   │
    │                └─────────────────────────┘
    │
    │ PostgreSQL Protocol (Port 5432)
    │
    │     ┌─────────────────────────────────────┐
    └─────┤  PostgreSQL (Shared)                │
          │   - User accounts                   │
          │   - Image metadata                  │
          │   - Job records                     │
          │   - Per-student schemas             │
          └─────────────────────────────────────┘
```

## Storage Layer: MinIO

**Why MinIO instead of filesystem storage?**

1. **S3-Compatible API**: Industry-standard interface used by AWS, Google Cloud, Azure
2. **Scalable**: Easily scales to petabytes of data across multiple servers
3. **Organized**: Bucket-based organization with folders and metadata
4. **Durable**: Built-in data integrity checks and replication
5. **Production-Ready**: Used by major companies for production workloads

**Key Concepts:**
- **Buckets**: Top-level containers (like folders but with global namespace)
- **Objects**: Individual files stored in buckets
- **Keys**: Unique identifiers for objects (like file paths)
- **Metadata**: Key-value tags attached to objects

**Example MinIO Operations:**
```python
# Create a bucket
minio_client.make_bucket("images")

# Upload an image
minio_client.put_object(
    bucket_name="images",
    object_name="users/123/photo.jpg",
    data=image_bytes,
    length=len(image_bytes),
    content_type="image/jpeg"
)

# Download an image
data = minio_client.get_object("images", "users/123/photo.jpg")
image_bytes = data.read()
```

## Cache Layer: Redis

**Why Redis?**

1. **In-Memory Speed**: Sub-millisecond response times
2. **Versatile Data Structures**: Strings, hashes, lists, sets, sorted sets
3. **Persistence**: Can save data to disk for durability
4. **Pub/Sub**: Built-in message broker for job queues
5. **Atomic Operations**: Thread-safe operations for concurrent access

**Use Cases in LAB04:**

### 1. Session Management
Store user login state without hitting the database on every request:
```python
# Store session
redis_client.setex(
    f"session:{session_id}",
    3600,  # 1 hour TTL
    json.dumps({"user_id": 123, "username": "alice"})
)

# Retrieve session
session_data = redis_client.get(f"session:{session_id}")
```

### 2. Thumbnail Caching
Cache resized thumbnails to avoid reprocessing:
```python
# Store thumbnail
redis_client.setex(
    f"thumbnail:{image_id}",
    86400,  # 24 hours TTL
    thumbnail_bytes
)

# Retrieve thumbnail
thumbnail = redis_client.get(f"thumbnail:{image_id}")
if thumbnail is None:
    # Generate and cache
    thumbnail = generate_thumbnail(image_id)
    redis_client.setex(f"thumbnail:{image_id}", 86400, thumbnail)
```

### 3. Job Queue
Queue processing jobs for asynchronous execution:
```python
# Add job to queue
job = {
    "job_id": 456,
    "image_id": 123,
    "operation": "grayscale",
    "user_id": 789
}
redis_client.rpush("job_queue", json.dumps(job))

# Worker retrieves job
job_data = redis_client.blpop("job_queue", timeout=5)
if job_data:
    process_job(json.loads(job_data[1]))
```

## Database Layer: PostgreSQL

**Why PostgreSQL?**

1. **ACID Compliance**: Reliable transactions and data integrity
2. **Relational**: Complex queries with joins across tables
3. **Mature**: 25+ years of development and optimization
4. **Rich Features**: JSON support, full-text search, spatial data
5. **Open Source**: No vendor lock-in, large ecosystem

**Why Shared Database?**

In this lab, PostgreSQL is shared across all students to simulate:
- **Multi-tenant applications**: One database serving many users
- **Shared resources**: Cost-effective infrastructure
- **Isolation through schemas**: Each student has their own namespace
- **Realistic production setup**: Most companies don't run a database per customer

**Schema Isolation:**
Each student gets their own schema (namespace) within the shared database:
```sql
-- Student alice's schema
CREATE SCHEMA alice;
CREATE TABLE alice.users (...);
CREATE TABLE alice.images (...);

-- Student bob's schema
CREATE SCHEMA bob;
CREATE TABLE bob.users (...);
CREATE TABLE bob.images (...);
```

This provides:
- **Data isolation**: Students can't see each other's data
- **Name isolation**: Same table names in different schemas
- **Shared infrastructure**: One PostgreSQL instance for all students
- **Simple management**: One database to backup, monitor, and maintain

**Key Tables:**

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Stores user accounts. Passwords are hashed (never stored in plaintext).

### Images Table
```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    original_filename VARCHAR(255) NOT NULL,
    minio_key VARCHAR(255) NOT NULL,
    file_size INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Stores metadata about uploaded images. The actual image data is in MinIO.

### Jobs Table
```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    image_id INTEGER REFERENCES images(id),
    operation VARCHAR(50) NOT NULL,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    result_minio_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

Tracks image processing jobs with their status and results.

## Data Flow Example

### User Uploads and Processes an Image

1. **User uploads image** (POST /api/upload)
   - Frontend receives image file
   - Frontend uploads to MinIO → `images/user_123/original_456.jpg`
   - Frontend creates record in PostgreSQL images table
   - Frontend returns `image_id=456` to user

2. **User requests processing** (POST /api/process)
   - Frontend creates job record in PostgreSQL
   - Frontend adds job to Redis queue
   - Frontend returns `job_id=789` to user

3. **Frontend processes job asynchronously**
   - Frontend worker thread polls Redis queue
   - Retrieves job `job_id=789`
   - Reads original image from MinIO
   - Calls image processor via gRPC (same as LAB03)
   - Processor returns processed image data
   - Frontend uploads result to MinIO → `images/user_123/processed_789.jpg`
   - Frontend updates job record in PostgreSQL (status=completed)

4. **User views result** (GET /api/jobs/789)
   - Frontend queries PostgreSQL for job status
   - If completed, frontend generates thumbnail
   - Caches thumbnail in Redis
   - Returns result to user

5. **User views gallery** (GET /api/images)
   - Frontend queries PostgreSQL for user's images
   - For each image, checks Redis for cached thumbnail
   - If not cached, generates thumbnail and caches it
   - Returns list of images with thumbnails

## Performance Considerations

### Why Not Just Use PostgreSQL for Everything?

**Images in PostgreSQL:**
- ❌ Binary data bloats database size
- ❌ Backup/restore times increase dramatically
- ❌ Query performance degrades with large blobs
- ❌ Not designed for streaming large files

**Sessions in PostgreSQL:**
- ❌ Database hit on every request
- ❌ Table locks on session updates
- ❌ Not optimized for high-frequency reads/writes

**Job Queue in PostgreSQL:**
- ❌ Polling creates constant database load
- ❌ No built-in pub/sub notification
- ❌ Lock contention with multiple workers

### The Right Tool for the Job

**MinIO for Images:**
- ✅ Optimized for large binary files
- ✅ Streaming support for efficient transfers
- ✅ Separate from database for better scaling
- ✅ S3 API compatibility

**Redis for Sessions/Cache:**
- ✅ In-memory speed (microseconds)
- ✅ Built-in expiration (TTL)
- ✅ Atomic operations for concurrent access
- ✅ Pub/sub for job queue notifications

**PostgreSQL for Metadata:**
- ✅ Complex queries with joins
- ✅ ACID transactions for data integrity
- ✅ Structured data with relationships
- ✅ Indexing for fast lookups

## Learning Objectives

By completing this lab, you will understand:

1. **Storage Patterns**: When to use object storage vs. database vs. cache
2. **Service Composition**: How multiple specialized services work together
3. **Data Flow**: How data moves between storage layers
4. **Persistence**: How volumes preserve data across container restarts
5. **Multi-Tenancy**: How to isolate data in shared infrastructure
6. **Performance**: How caching and queuing improve application responsiveness
7. **Production Patterns**: Real-world architectures used by major companies

## Real-World Applications

This architecture pattern is used by:

- **Photo Sharing Apps**: Instagram, Flickr (S3 + Redis + PostgreSQL)
- **Video Platforms**: YouTube, Netflix (Object Storage + Cache + Database)
- **Cloud Storage**: Dropbox, Google Drive (Distributed Object Storage)
- **E-commerce**: Amazon, eBay (Redis Sessions + Database + S3)
- **Social Networks**: Facebook, Twitter (Multiple storage layers)

The skills you learn in this lab directly translate to production systems at scale.
