# LAB04 - Redis Cache and Sessions

This document provides detailed information about using Redis for caching, sessions, and job queues in LAB04.

## What is Redis?

Redis (Remote Dictionary Server) is an in-memory data structure store used as a database, cache, and message broker.

**Key Features:**
- **In-Memory**: Data stored in RAM for microsecond latency
- **Persistent**: Optional disk persistence for durability
- **Data Structures**: Strings, hashes, lists, sets, sorted sets, and more
- **Atomic Operations**: Thread-safe operations for concurrent access
- **Pub/Sub**: Built-in publish/subscribe messaging
- **TTL Support**: Automatic key expiration

## Use Cases in LAB04

### 1. Session Management

Store user authentication state without hitting the database on every request.

**Why Redis for Sessions?**
- ✅ Very fast (sub-millisecond reads)
- ✅ Automatic expiration (TTL)
- ✅ Scales horizontally
- ✅ No database overhead

**Session Flow:**
```
1. User logs in → Create session → Store in Redis
2. User makes request → Check Redis for session → Verify user
3. Session expires → Redis auto-deletes → User must re-login
```

### 2. Thumbnail Caching

Cache generated thumbnails to avoid regenerating them repeatedly.

**Why Cache Thumbnails?**
- ✅ Image processing is expensive (CPU intensive)
- ✅ Thumbnails requested frequently (gallery views)
- ✅ Same thumbnail used multiple times
- ✅ RAM access much faster than disk/network

**Cache Flow:**
```
1. Request thumbnail → Check Redis cache
2. If cached → Return immediately (fast)
3. If not cached → Generate → Store in cache → Return
4. Cache expires after 24 hours → Regenerate if requested
```

### 3. Job Queue

Queue image processing jobs for asynchronous execution.

**Why Redis for Job Queue?**
- ✅ FIFO list data structure (queue)
- ✅ Blocking operations (wait for jobs)
- ✅ Atomic push/pop (thread-safe)
- ✅ Simple and reliable

**Queue Flow:**
```
1. User requests processing → Create job → Push to Redis queue
2. Worker polls queue → Pop job → Process image
3. Worker updates job status in database
4. User polls status → Shows completion
```

## Python Integration

### Installation

Already included in `requirements.txt`:
```
redis==5.0.1
```

### Configuration

```python
import redis
import os

# Create Redis client
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=0,  # Database number (0-15)
    decode_responses=True  # Automatically decode bytes to strings
)

# Test connection
try:
    redis_client.ping()
    print("Connected to Redis")
except redis.ConnectionError:
    print("Failed to connect to Redis")
```

### Connection Pooling

Redis-py automatically uses connection pooling:

```python
# Connection pool is created automatically
redis_client = redis.Redis(
    host='redis',
    port=6379,
    max_connections=10  # Optional: limit connections
)

# Or create pool explicitly
pool = redis.ConnectionPool(
    host='redis',
    port=6379,
    max_connections=10
)
redis_client = redis.Redis(connection_pool=pool)
```

## Session Management

### Store Session

```python
import json
from datetime import timedelta

def create_session(user_id, username):
    """Create a user session"""
    session_id = secrets.token_urlsafe(32)  # Generate random session ID
    
    session_data = {
        'user_id': user_id,
        'username': username,
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Store session with 1 hour expiration
    redis_client.setex(
        name=f"session:{session_id}",
        time=timedelta(hours=1),
        value=json.dumps(session_data)
    )
    
    return session_id
```

### Retrieve Session

```python
def get_session(session_id):
    """Get session data"""
    session_json = redis_client.get(f"session:{session_id}")
    
    if session_json:
        return json.loads(session_json)
    return None
```

### Extend Session

```python
def extend_session(session_id):
    """Extend session expiration"""
    # Extend by another hour
    redis_client.expire(f"session:{session_id}", timedelta(hours=1))
```

### Delete Session (Logout)

```python
def delete_session(session_id):
    """Delete a session (logout)"""
    redis_client.delete(f"session:{session_id}")
```

### Session Middleware (Flask)

```python
from functools import wraps
from flask import request, jsonify

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        session_data = get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session expired'}), 401
        
        # Extend session on activity
        extend_session(session_id)
        
        # Add user data to request
        request.user_id = session_data['user_id']
        request.username = session_data['username']
        
        return f(*args, **kwargs)
    
    return decorated_function

# Usage
@app.route('/api/profile')
@require_auth
def profile():
    return jsonify({
        'user_id': request.user_id,
        'username': request.username
    })
```

**Security Note:** When setting session cookies, always use:
- `httponly=True` - Prevents JavaScript access (XSS protection)
- `secure=True` - Only send over HTTPS (in production)
- `samesite='Lax'` - CSRF protection

```python
response.set_cookie(
    'session_id',
    session_id,
    httponly=True,
    secure=True,  # IMPORTANT: Only over HTTPS
    samesite='Lax',
    max_age=3600
)
```

## Thumbnail Caching

### Store Thumbnail

```python
def cache_thumbnail(image_id, thumbnail_bytes, size='small'):
    """Cache a thumbnail"""
    key = f"thumbnail:{image_id}:{size}"
    
    # Store with 24 hour expiration
    redis_client.setex(
        name=key,
        time=timedelta(hours=24),
        value=thumbnail_bytes
    )
```

### Retrieve Thumbnail

```python
def get_cached_thumbnail(image_id, size='small'):
    """Get cached thumbnail"""
    key = f"thumbnail:{image_id}:{size}"
    return redis_client.get(key)
```

### Get or Generate Thumbnail

```python
from PIL import Image
import io

def get_thumbnail(image_id, size='small'):
    """Get thumbnail, generating if not cached"""
    # Try cache first
    cached = get_cached_thumbnail(image_id, size)
    if cached:
        return cached
    
    # Not cached, generate it
    # 1. Load original image from MinIO
    original_data = minio_client.get_object('images', f'original_{image_id}.jpg')
    original_image = Image.open(io.BytesIO(original_data.read()))
    
    # 2. Resize
    sizes = {'small': (150, 150), 'medium': (300, 300)}
    thumbnail = original_image.copy()
    thumbnail.thumbnail(sizes.get(size, (150, 150)))
    
    # 3. Convert to bytes
    buffer = io.BytesIO()
    thumbnail.save(buffer, format='JPEG', quality=85)
    thumbnail_bytes = buffer.getvalue()
    
    # 4. Cache for next time
    cache_thumbnail(image_id, thumbnail_bytes, size)
    
    return thumbnail_bytes
```

### Invalidate Cache

```python
def invalidate_thumbnail(image_id):
    """Remove all cached thumbnails for an image"""
    # Delete all size variants
    keys = redis_client.keys(f"thumbnail:{image_id}:*")
    if keys:
        redis_client.delete(*keys)
```

## Job Queue

### Add Job to Queue

```python
import json

def enqueue_job(job_id, image_id, operation, parameters):
    """Add a processing job to the queue"""
    job_data = {
        'job_id': job_id,
        'image_id': image_id,
        'operation': operation,
        'parameters': parameters,
        'enqueued_at': datetime.utcnow().isoformat()
    }
    
    # Push to end of list (FIFO queue)
    redis_client.rpush('job_queue', json.dumps(job_data))
    
    # Also store job status
    redis_client.setex(
        f"job:{job_id}:status",
        timedelta(hours=24),
        'queued'
    )
```

### Process Jobs (Worker)

```python
def process_jobs():
    """Worker that processes jobs from queue"""
    print("Worker started, waiting for jobs...")
    
    while True:
        # Block until job available (timeout after 5 seconds)
        job_data = redis_client.blpop('job_queue', timeout=5)
        
        if job_data:
            # job_data is a tuple: (queue_name, job_json)
            job = json.loads(job_data[1])
            
            try:
                # Update status
                redis_client.setex(
                    f"job:{job['job_id']}:status",
                    timedelta(hours=24),
                    'processing'
                )
                
                # Process the image
                process_image(
                    job['image_id'],
                    job['operation'],
                    job['parameters']
                )
                
                # Update status
                redis_client.setex(
                    f"job:{job['job_id']}:status",
                    timedelta(hours=24),
                    'completed'
                )
                
            except Exception as e:
                print(f"Error processing job {job['job_id']}: {e}")
                redis_client.setex(
                    f"job:{job['job_id']}:status",
                    timedelta(hours=24),
                    'failed'
                )
```

### Check Job Status

```python
def get_job_status(job_id):
    """Get current status of a job"""
    status = redis_client.get(f"job:{job_id}:status")
    return status if status else 'unknown'
```

### Get Queue Length

```python
def get_queue_length():
    """Get number of jobs waiting in queue"""
    return redis_client.llen('job_queue')
```

## Data Structures

### Strings (Simple Key-Value)

```python
# Set
redis_client.set('key', 'value')

# Get
value = redis_client.get('key')

# Set with expiration
redis_client.setex('key', timedelta(hours=1), 'value')

# Increment (atomic)
redis_client.incr('counter')
redis_client.incrby('counter', 10)
```

### Hashes (Object Storage)

```python
# Set hash fields
redis_client.hset('user:123', mapping={
    'username': 'alice',
    'email': 'alice@example.com',
    'score': 100
})

# Get single field
username = redis_client.hget('user:123', 'username')

# Get all fields
user_data = redis_client.hgetall('user:123')

# Increment field
redis_client.hincrby('user:123', 'score', 10)
```

### Lists (Queues)

```python
# Push to end (enqueue)
redis_client.rpush('queue', 'job1')
redis_client.rpush('queue', 'job2')

# Pop from beginning (dequeue)
job = redis_client.lpop('queue')

# Blocking pop (wait for item)
job = redis_client.blpop('queue', timeout=5)

# Get list length
length = redis_client.llen('queue')

# Get range
items = redis_client.lrange('queue', 0, -1)  # All items
```

### Sets (Unique Collections)

```python
# Add members
redis_client.sadd('tags:image:123', 'nature', 'landscape', 'sunset')

# Check membership
is_member = redis_client.sismember('tags:image:123', 'nature')

# Get all members
tags = redis_client.smembers('tags:image:123')

# Remove member
redis_client.srem('tags:image:123', 'sunset')

# Set operations
redis_client.sinter('tags:image:123', 'tags:image:456')  # Intersection
redis_client.sunion('tags:image:123', 'tags:image:456')  # Union
```

### Sorted Sets (Leaderboards)

```python
# Add with score
redis_client.zadd('leaderboard', {'alice': 100, 'bob': 85, 'charlie': 92})

# Get rank (0-based)
rank = redis_client.zrank('leaderboard', 'alice')

# Get score
score = redis_client.zscore('leaderboard', 'alice')

# Get top N
top_players = redis_client.zrevrange('leaderboard', 0, 9, withscores=True)

# Increment score
redis_client.zincrby('leaderboard', 10, 'alice')
```

## Performance Tips

### 1. Use Pipelines for Multiple Operations

```python
# Without pipeline (multiple round trips)
redis_client.set('key1', 'value1')
redis_client.set('key2', 'value2')
redis_client.set('key3', 'value3')

# With pipeline (single round trip)
pipe = redis_client.pipeline()
pipe.set('key1', 'value1')
pipe.set('key2', 'value2')
pipe.set('key3', 'value3')
pipe.execute()
```

### 2. Use Appropriate Data Structures

```python
# Bad - separate keys for user fields
redis_client.set('user:123:username', 'alice')
redis_client.set('user:123:email', 'alice@example.com')

# Good - hash for related fields
redis_client.hset('user:123', mapping={
    'username': 'alice',
    'email': 'alice@example.com'
})
```

### 3. Set Expiration on Keys

```python
# Prevent memory leaks
redis_client.setex('temp_data', timedelta(minutes=5), 'value')

# Or set TTL after creation
redis_client.set('key', 'value')
redis_client.expire('key', timedelta(minutes=5))
```

### 4. Use Key Patterns

```python
# Good key naming
redis_client.set('session:abc123', session_data)
redis_client.set('thumbnail:456:small', thumbnail_data)
redis_client.set('job:789:status', 'completed')

# Makes it easy to find related keys
session_keys = redis_client.keys('session:*')
thumbnail_keys = redis_client.keys('thumbnail:*:small')
```

## Monitoring

### Check Memory Usage

```python
info = redis_client.info('memory')
print(f"Used memory: {info['used_memory_human']}")
print(f"Peak memory: {info['used_memory_peak_human']}")
```

### Get Key Count

```python
dbsize = redis_client.dbsize()
print(f"Total keys: {dbsize}")
```

### Check Specific Keys

```python
# Find keys by pattern
keys = redis_client.keys('session:*')
print(f"Active sessions: {len(keys)}")

# Check TTL
ttl = redis_client.ttl('session:abc123')
print(f"Session expires in {ttl} seconds")
```

## Common Issues

### Issue: "Connection refused"

**Solution:** Check:
- Redis container is running
- Correct hostname (use service name in Docker)
- Services on same network

```bash
docker compose ps
docker compose logs redis
```

### Issue: "Memory usage too high"

**Solution:** Set expiration on keys:
```python
# Always set TTL to prevent memory leaks
redis_client.setex('key', timedelta(hours=1), 'value')
```

### Issue: "Keys not expiring"

**Solution:** Check TTL is set:
```python
ttl = redis_client.ttl('key')
if ttl == -1:
    print("Key has no expiration!")
    redis_client.expire('key', timedelta(hours=1))
```

### Issue: "Queue growing indefinitely"

**Solution:** Make sure worker is running:
```bash
# Check worker logs
docker compose logs imgprocessor

# Check queue length
redis_client.llen('job_queue')
```

## Testing

### Unit Tests with Fakeredis

```python
import fakeredis
import pytest

@pytest.fixture
def redis_client():
    """Create a fake Redis client for testing"""
    return fakeredis.FakeRedis(decode_responses=True)

def test_session_creation(redis_client):
    session_id = create_session(redis_client, 123, 'alice')
    assert session_id is not None
    
    session = get_session(redis_client, session_id)
    assert session['user_id'] == 123
    assert session['username'] == 'alice'
```

### Integration Tests with Real Redis

```python
def test_job_queue_integration():
    # Clear queue before test
    redis_client.delete('job_queue')
    
    # Enqueue job
    enqueue_job(1, 123, 'grayscale', {})
    
    # Check queue
    assert redis_client.llen('job_queue') == 1
    
    # Process job
    job_data = redis_client.lpop('job_queue')
    assert job_data is not None
```

## Summary

Redis provides:
- ✅ Sub-millisecond latency for cache lookups
- ✅ Automatic key expiration for sessions
- ✅ Reliable job queue with blocking operations
- ✅ Atomic operations for concurrent access
- ✅ Flexible data structures for various use cases

For more details, see the [Redis documentation](https://redis.io/documentation).
