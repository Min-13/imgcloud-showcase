# LAB04 - Troubleshooting Guide

This document provides solutions to common issues you may encounter in LAB04.

## Service Connectivity Issues

### MinIO: "Connection refused" or "Bucket does not exist"

**Symptoms:**
- Frontend logs show "Failed to connect to MinIO"
- Image uploads fail with connection errors
- MinIO operations timeout

**Solutions:**

1. **Check MinIO container is running:**
```bash
docker compose ps
# Should show minio container as "Up"
```

2. **Check MinIO logs:**
```bash
docker compose logs STUDENTNAME-minio
# Look for "MinIO Object Storage Server" message
```

3. **Verify MinIO hostname in frontend:**
```yaml
# In docker-compose.yml
environment:
  - MINIO_HOST=STUDENTNAME-minio  # Must match service name
```

4. **Create bucket on startup:**
```python
# In app.py initialization
from minio import Minio
from minio.error import S3Error

try:
    if not minio_client.bucket_exists("images"):
        minio_client.make_bucket("images")
        print("Created images bucket")
except S3Error as e:
    print(f"MinIO error: {e}")
```

5. **Verify services on same network:**
```yaml
# Both services must use same network
networks:
  - STUDENTNAME-network
```

### Redis: "Connection refused" or "No connection"

**Symptoms:**
- Session management fails
- Cache lookups return errors
- Job queue not working

**Solutions:**

1. **Check Redis container:**
```bash
docker compose ps
docker compose logs STUDENTNAME-redis
# Look for "Ready to accept connections"
```

2. **Test Redis connectivity:**
```bash
# From frontend container
docker compose exec STUDENTNAME-frontend sh
pip install redis
python -c "import redis; r=redis.Redis(host='STUDENTNAME-redis'); print(r.ping())"
```

3. **Verify Redis configuration:**
```yaml
environment:
  - REDIS_HOST=STUDENTNAME-redis  # Must match service name
  - REDIS_PORT=6379
```

4. **Check Redis is not password protected:**
```yaml
# In docker-compose.yml (no AUTH required for local dev)
STUDENTNAME-redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
  # No requirepass
```

### PostgreSQL: "Could not connect to server" or "authentication failed"

**Symptoms:**
- Database queries fail
- User registration/login doesn't work
- Schema errors

**Solutions:**

1. **Verify DATABASE_URL is correct:**
```bash
# Check environment variable
docker compose exec STUDENTNAME-frontend env | grep DATABASE_URL
```

2. **Test PostgreSQL connection:**
```python
# From Python
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("Database connected!")
except Exception as e:
    print(f"Connection failed: {e}")
```

3. **Check schema exists:**
```sql
-- Connect to PostgreSQL
\dn  -- List schemas
-- Should show your STUDENTNAME schema
```

4. **Verify search_path is set:**
```python
# In SQLAlchemy connection
engine = create_engine(
    DATABASE_URL,
    connect_args={'options': f'-csearch_path={DB_SCHEMA}'}
)
```

5. **Check table permissions:**
```sql
-- Grant permissions (instructor should do this)
GRANT ALL PRIVILEGES ON SCHEMA studentname TO studentname;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA studentname TO studentname;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA studentname TO studentname;
```

## Docker Compose Issues

### "Service name must be unique"

**Symptom:** Error when running `docker compose up`

**Solution:** Ensure all service names include your STUDENTNAME:
```yaml
services:
  STUDENTNAME-frontend:    # Not just "frontend"
  STUDENTNAME-imgprocessor:
  STUDENTNAME-minio:
  STUDENTNAME-redis:
```

### "Port is already allocated"

**Symptom:** Cannot start frontend due to port conflict

**Solution:**
1. Check if another container is using the port:
```bash
docker ps | grep YOUR_PORT
```

2. Stop conflicting container:
```bash
docker stop <container_id>
```

3. Verify your assigned port:
```bash
cat PORTS.md  # Check your assigned port range
```

### "Network not found"

**Symptom:** Services can't find network

**Solution:** Define network in docker-compose.yml:
```yaml
networks:
  STUDENTNAME-network:
    driver: bridge
```

### "Volume not found" or "Permission denied on volume"

**Symptom:** Container can't access volume

**Solution:**
```bash
# List volumes
docker volume ls

# Remove and recreate
docker compose down -v
docker compose up -d
```

## Application Issues

### Images upload but can't be viewed

**Symptoms:**
- Upload succeeds
- Download/view fails
- MinIO shows object exists

**Solutions:**

1. **Check minio_key is stored correctly:**
```python
# Should store the key returned by MinIO
minio_key = upload_to_minio(image_data)
db.create_image(user_id, filename, minio_key)  # Save this key!
```

2. **Verify download uses correct key:**
```python
# Use the exact key from database
image_record = db.get_image(image_id)
image_data = minio_client.get_object('images', image_record.minio_key)
```

3. **Check content type:**
```python
# Set correct content type on upload
minio_client.put_object(
    bucket_name='images',
    object_name=minio_key,
    data=image_data,
    length=len(image_data),
    content_type='image/jpeg'  # Important!
)
```

### Sessions not persisting (users logged out immediately)

**Symptoms:**
- Users can log in but immediately logged out
- Session cookie not set
- Redis shows no sessions

**Solutions:**

1. **Set session cookie correctly:**
```python
from flask import make_response

@app.route('/api/login', methods=['POST'])
def login():
    # Authenticate user
    session_id = create_session(user_id, username)
    
    # Create response with cookie
    response = make_response(jsonify({'success': True}))
    response.set_cookie(
        'session_id',
        session_id,
        httponly=True,
        max_age=3600  # 1 hour
    )
    return response
```

2. **Check cookie in subsequent requests:**
```python
from flask import request

session_id = request.cookies.get('session_id')
if session_id:
    session = get_session(session_id)
```

3. **Verify Redis TTL:**
```python
# Set expiration when creating session
redis_client.setex(
    f"session:{session_id}",
    timedelta(hours=1),  # Must set expiration!
    json.dumps(session_data)
)
```

### Jobs stay in "pending" status forever

**Symptoms:**
- Processing jobs never complete
- Queue has jobs but nothing happens
- Worker not processing

**Solutions:**

1. **Check imgprocessor is running:**
```bash
docker compose ps
# imgprocessor should be "Up"
```

2. **Check worker is polling queue:**
```bash
docker compose logs STUDENTNAME-imgprocessor
# Should show "Waiting for jobs..." or similar
```

3. **Verify job is in queue:**
```python
# Check Redis queue length
queue_length = redis_client.llen('job_queue')
print(f"Jobs in queue: {queue_length}")
```

4. **Check job data format:**
```python
# Job must be valid JSON
job_data = {
    'job_id': 123,
    'image_id': 456,
    'operation': 'grayscale',
    'parameters': {}
}
redis_client.rpush('job_queue', json.dumps(job_data))
```

5. **Check worker error logs:**
```bash
docker compose logs STUDENTNAME-imgprocessor
# Look for exception traces
```

### Thumbnails not caching (slow gallery loads)

**Symptoms:**
- Gallery loads slowly every time
- Redis not storing thumbnails
- Memory usage not increasing

**Solutions:**

1. **Verify cache is being set:**
```python
# In thumbnail generation
thumbnail_bytes = generate_thumbnail(image_id)
redis_client.setex(
    f"thumbnail:{image_id}:small",
    timedelta(hours=24),
    thumbnail_bytes
)
```

2. **Check cache is being read:**
```python
# Before generating thumbnail
cached = redis_client.get(f"thumbnail:{image_id}:small")
if cached:
    return cached  # Return cached version
```

3. **Verify TTL is reasonable:**
```python
# Don't use too short TTL
redis_client.setex(
    key,
    timedelta(hours=24),  # At least a few hours
    data
)
```

4. **Check Redis memory:**
```python
info = redis_client.info('memory')
print(f"Used: {info['used_memory_human']}")
```

## Performance Issues

### Slow image uploads

**Solutions:**

1. **Use streaming for large files:**
```python
# Instead of loading entire file
image_data = request.files['image'].read()  # Bad for large files

# Stream directly
file = request.files['image']
minio_client.put_object(
    'images',
    minio_key,
    file.stream,
    length=file.content_length
)
```

2. **Check network between services:**
```bash
# Test network speed
docker compose exec STUDENTNAME-frontend sh
time wget http://STUDENTNAME-minio:9000
```

### Database queries slow

**Solutions:**

1. **Add indexes to frequently queried columns:**
```sql
CREATE INDEX idx_images_user_id ON images(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
```

2. **Use connection pooling:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)
```

3. **Limit query results:**
```python
# Don't fetch all rows
images = session.query(Image)\
    .filter_by(user_id=user_id)\
    .limit(50)\
    .all()
```

## Data Issues

### Data not persisting after restart

**Symptoms:**
- Users/images lost after `docker compose down`
- Redis cache empty after restart
- MinIO files disappear

**Solutions:**

1. **Verify volumes are defined:**
```yaml
volumes:
  STUDENTNAME-minio-data:
  STUDENTNAME-redis-data:

services:
  STUDENTNAME-minio:
    volumes:
      - STUDENTNAME-minio-data:/data
  
  STUDENTNAME-redis:
    volumes:
      - STUDENTNAME-redis-data:/data
```

2. **Don't use `-v` flag when stopping:**
```bash
# This keeps volumes (good)
docker compose down

# This deletes volumes (bad - loses data)
docker compose down -v
```

3. **Check volumes exist:**
```bash
docker volume ls | grep STUDENTNAME
```

### PostgreSQL data lost after schema changes

**Symptom:** Tables don't exist after restart

**Solution:**

1. **Use SQLAlchemy migrations (Alembic):**
```python
# Initialize database on startup
Base.metadata.create_all(bind=engine)
```

2. **Or manually create schema:**
```sql
CREATE SCHEMA IF NOT EXISTS studentname;
CREATE TABLE IF NOT EXISTS studentname.users (...);
```

## Health Check Issues

### Health endpoint shows services unhealthy

**Solutions:**

1. **Check individual service health:**
```bash
# Test each service directly
curl http://localhost:YOUR_PORT/health
docker compose exec STUDENTNAME-frontend wget -O- http://STUDENTNAME-minio:9000/minio/health/live
docker compose exec STUDENTNAME-frontend redis-cli -h STUDENTNAME-redis ping
```

2. **Add timeout to health checks:**
```python
import requests

try:
    response = requests.get(
        f'{PROCESSOR_URL}/health',
        timeout=2  # Don't wait forever
    )
    healthy = response.status_code == 200
except requests.Timeout:
    healthy = False
```

## Debugging Tips

### 1. Check All Logs

```bash
# View all logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# Filter to specific service
docker compose logs STUDENTNAME-frontend

# Show last 50 lines
docker compose logs --tail=50
```

### 2. Execute Commands in Container

```bash
# Shell into frontend
docker compose exec STUDENTNAME-frontend sh

# Test connections from inside
wget http://STUDENTNAME-minio:9000
redis-cli -h STUDENTNAME-redis ping
```

### 3. Check Environment Variables

```bash
docker compose exec STUDENTNAME-frontend env
# Verify all environment variables are set correctly
```

### 4. Inspect Docker Network

```bash
# List networks
docker network ls

# Inspect your network
docker network inspect <network-name>
# Should show all your services
```

### 5. Check Resource Usage

```bash
# See CPU/memory usage
docker stats

# Check disk space
df -h
```

## Getting Help

If you're still stuck:

1. **Check logs carefully** - Most issues show up in logs
2. **Compare with working example** - Review solution docker-compose.yml
3. **Test services individually** - Isolate the problem
4. **Ask instructor** - Provide specific error messages and logs

### Information to Provide When Asking for Help

- Output of `docker compose ps`
- Relevant logs from `docker compose logs`
- Your docker-compose.yml (if not working)
- Specific error messages
- What you've already tried

## Summary

Most issues fall into these categories:

1. **Connectivity**: Services can't reach each other → Check network and service names
2. **Configuration**: Wrong environment variables → Verify all env vars
3. **Volumes**: Data not persisting → Check volume definitions
4. **Permissions**: Access denied → Check credentials and permissions
5. **Resources**: Out of memory/disk → Clean up old containers/images

**General debugging workflow:**
1. Check if services are running (`docker compose ps`)
2. Check logs for errors (`docker compose logs`)
3. Test connectivity between services
4. Verify configuration (environment variables)
5. Check data persistence (volumes)
