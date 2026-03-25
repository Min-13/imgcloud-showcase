# LAB04: Testing Your Implementation

This guide provides comprehensive testing procedures for your LAB04 implementation. Use these tests to verify each component works correctly before submission.

## Quick Testing Workflow

### 1. Check Services Are Running

After starting your services with `docker compose up -d`, verify all containers are running:

```bash
docker compose ps
```

**Expected output:** All services should show status "Up":
- `STUDENTNAME-frontend` (Up)
- `STUDENTNAME-imgprocessor` (Up)
- `STUDENTNAME-minio` (Up)
- `STUDENTNAME-redis` (Up)

**If a service is not running:**
```bash
# Check logs for the failed service
docker compose logs STUDENTNAME-servicename

# Common issues:
# - Port already in use (change YOUR_PORT in docker-compose.yml)
# - Missing environment variables (check LAB04-ENVIRONMENT-VARIABLES.md)
# - Network conflicts (ensure unique STUDENTNAME prefix)
```

### 2. Test Health Endpoints

Verify the frontend can communicate with all services:

```bash
curl http://localhost:YOUR_PORT/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "message": "Frontend is running",
  "services": {
    "processor": "healthy",
    "minio": "healthy",
    "redis": "healthy",
    "database": "healthy"
  },
  "lab04_features": true
}
```

**If lab04_features is false:**
- Check that all LAB04 environment variables are set
- Verify DATABASE_URL is correct
- Confirm MinIO and Redis services are running

### 3. Test User Registration

Register a new user account (stored in PostgreSQL):

```bash
curl -X POST http://localhost:YOUR_PORT/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

**Expected response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": 1
}
```

**Common errors:**
- `"Database not configured"` - DATABASE_URL environment variable is missing or incorrect
- `"Username already exists"` - User already registered, try a different username
- `"Password must be at least 8 characters"` - Use a longer password

### 4. Test User Login

Authenticate and receive a session cookie (stored in Redis):

```bash
curl -X POST http://localhost:YOUR_PORT/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' \
  -c cookies.txt
```

**Expected response:**
```json
{
  "success": true,
  "message": "Logged in successfully",
  "user": {
    "id": 1,
    "username": "testuser"
  }
}
```

**The cookies.txt file:**
- Contains your session ID
- Use `-b cookies.txt` in subsequent requests for authentication
- Session expires after 1 hour (SESSION_TIMEOUT)

### 5. Verify Session

Confirm your session is valid:

```bash
curl -b cookies.txt http://localhost:YOUR_PORT/api/user
```

**Expected response:**
```json
{
  "user_id": 1,
  "username": "testuser"
}
```

### 6. Test Image Upload

Upload an image to MinIO:

```bash
# Create a test image if you don't have one
convert -size 100x100 xc:blue test.png  # Requires ImageMagick

# Upload the image
curl -b cookies.txt -F "image=@test.png" \
  http://localhost:YOUR_PORT/api/upload
```

**Expected response:**
```json
{
  "success": true,
  "image_id": 1,
  "filename": "test.png",
  "size": 12345
}
```

**This test verifies:**
- ✅ MinIO is accepting connections
- ✅ Images are being stored in the correct bucket
- ✅ PostgreSQL is storing image metadata
- ✅ Authentication is working

### 7. List Uploaded Images

Retrieve your image history from the database:

```bash
curl -b cookies.txt http://localhost:YOUR_PORT/api/images
```

**Expected response:**
```json
{
  "images": [
    {
      "id": 1,
      "filename": "test.png",
      "size": 12345,
      "upload_date": "2026-02-05T00:00:00"
    }
  ]
}
```

### 8. Test Image Processing (LAB03 Endpoint)

The `/process` endpoint should still work without authentication:

```bash
curl -F "image=@test.png" \
  -F "operation=grayscale" \
  http://localhost:YOUR_PORT/process \
  --output result.png
```

**Expected result:**
- A grayscale version of your image is saved to `result.png`
- Verifies the C++ processor is working
- Tests backward compatibility with LAB03

### 9. Test Data Persistence

Verify volumes preserve data across container restarts:

```bash
# Stop all services
docker compose down

# Restart services
docker compose up -d

# Wait for services to start (check logs)
docker compose logs -f

# Verify user can still log in (data persisted in PostgreSQL)
curl -X POST http://localhost:YOUR_PORT/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' \
  -c cookies2.txt

# Verify images still exist (data persisted in MinIO volume)
curl -b cookies2.txt http://localhost:YOUR_PORT/api/images
```

**What this tests:**
- ✅ PostgreSQL data persists (user accounts, image metadata)
- ✅ MinIO volume preserves uploaded images
- ✅ Services can reconnect after restart

**Note:** Redis sessions do NOT persist across restarts by default, so you'll need to log in again (new session).

## Advanced Testing

### Test Redis Caching

Check that Redis is being used for sessions:

```bash
# Connect to Redis container
docker exec -it STUDENTNAME-redis redis-cli

# List all keys (should see session keys)
KEYS *

# Get a session (replace SESSION_ID with actual value from cookies.txt)
GET session:SESSION_ID

# Exit Redis CLI
exit
```

### Test MinIO Storage

Verify images are stored in MinIO:

```bash
# Access MinIO console (if you exposed port 9001)
# Open http://localhost:9001 in browser
# Login with MINIO_ACCESS_KEY and MINIO_SECRET_KEY

# Or use MinIO CLI
docker exec -it STUDENTNAME-minio mc alias set local http://localhost:9000 minioadmin minioadmin123
docker exec -it STUDENTNAME-minio mc ls local/images
```

### Test PostgreSQL Tables

Verify database schema and tables were created:

```bash
# Connect to your database
docker exec -it 420s26-postgres psql -U STUDENTNAME -d STUDENTNAME

# List schemas
\dn

# Set search path
SET search_path TO STUDENTNAME;

# List tables
\dt

# View users table
SELECT * FROM users;

# View images table
SELECT * FROM images;

# Exit psql
\q
```

**Expected tables:**
- `users` - User accounts
- `images` - Image metadata
- `jobs` - Processing jobs

### Performance Testing

Test multiple concurrent operations:

```bash
# Upload multiple images quickly
for i in {1..10}; do
  curl -b cookies.txt -F "image=@test.png" \
    http://localhost:YOUR_PORT/api/upload &
done
wait

# Verify all uploads succeeded
curl -b cookies.txt http://localhost:YOUR_PORT/api/images
```

## Troubleshooting Test Failures

### Health check fails

**Symptom:** `/health` shows services as "unavailable"

**Solutions:**
1. Check service status: `docker compose ps`
2. View service logs: `docker compose logs SERVICENAME`
3. Verify environment variables: `docker compose config`
4. Test individual service connections:
   ```bash
   # Test MinIO
   docker exec STUDENTNAME-frontend curl http://STUDENTNAME-minio:9000/minio/health/live
   
   # Test Redis
   docker exec STUDENTNAME-frontend redis-cli -h STUDENTNAME-redis ping
   
   # Test PostgreSQL
   docker exec STUDENTNAME-frontend psql -U STUDENTNAME -h 420s26-postgres -d STUDENTNAME -c "SELECT 1"
   ```

### Registration fails

**Symptom:** "Database not configured" error

**Solutions:**
1. Verify DATABASE_URL is set: `docker exec STUDENTNAME-frontend printenv DATABASE_URL`
2. Test database connection: `docker exec -it 420s26-postgres psql -U STUDENTNAME -d STUDENTNAME`
3. Check database exists: `docker exec -it 420s26-postgres psql -U postgres -c "\l" | grep STUDENTNAME`
4. Verify schema exists: `docker exec -it 420s26-postgres psql -U STUDENTNAME -d STUDENTNAME -c "\dn"`

### Upload fails

**Symptom:** "Storage services unavailable" error

**Solutions:**
1. Check MinIO is running: `docker compose ps STUDENTNAME-minio`
2. Verify MINIO_HOST matches service name in docker-compose.yml
3. Test MinIO health: `docker exec STUDENTNAME-minio curl http://localhost:9000/minio/health/live`
4. Check volume is mounted: `docker volume inspect STUDENTNAME-minio-data`

### Image processing fails

**Symptom:** Image processing returns error or times out

**Solutions:**
1. Check processor logs: `docker compose logs STUDENTNAME-imgprocessor`
2. Verify processor is running: `docker compose ps STUDENTNAME-imgprocessor`
3. Test gRPC connection from frontend to processor
4. Check image format is supported (JPEG, PNG)

### Data doesn't persist

**Symptom:** Data lost after `docker compose down`

**Solutions:**
1. Verify volumes are defined in docker-compose.yml
2. Don't use `docker compose down -v` (deletes volumes)
3. Check volumes exist: `docker volume ls | grep STUDENTNAME`
4. Inspect volume mounts: `docker inspect STUDENTNAME-minio`

## Pre-Submission Checklist

Before submitting, run through this checklist:

- [ ] All services start successfully (`docker compose up -d`)
- [ ] Health check shows all services healthy
- [ ] User registration works
- [ ] User login creates session
- [ ] Image upload stores in MinIO
- [ ] Image list shows uploaded images
- [ ] Image processing works
- [ ] Data persists after `docker compose down` and restart
- [ ] All container/service names use STUDENTNAME prefix
- [ ] No conflicts with other students' containers
- [ ] Logs show no errors or warnings
- [ ] Environment variables are correctly configured
- [ ] Volumes are properly named and mounted

## Automated Testing Script

Create a test script to run all tests automatically:

```bash
#!/bin/bash
# test_lab04.sh

set -e  # Exit on error

PORT=$1
if [ -z "$PORT" ]; then
  echo "Usage: $0 YOUR_PORT"
  exit 1
fi

echo "Testing LAB04 on port $PORT..."

# Test health
echo "1. Testing health endpoint..."
curl -s http://localhost:$PORT/health | jq .

# Register user
echo "2. Registering user..."
curl -s -X POST http://localhost:$PORT/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' | jq .

# Login
echo "3. Logging in..."
curl -s -X POST http://localhost:$PORT/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' \
  -c cookies.txt | jq .

# Upload image
echo "4. Uploading image..."
curl -s -b cookies.txt -F "image=@test.png" \
  http://localhost:$PORT/api/upload | jq .

# List images
echo "5. Listing images..."
curl -s -b cookies.txt http://localhost:$PORT/api/images | jq .

echo "All tests passed!"
```

Make it executable and run:
```bash
chmod +x test_lab04.sh
./test_lab04.sh YOUR_PORT
```

## Summary

Thorough testing ensures:
- All services are properly configured and communicating
- Data persistence works correctly
- Authentication and authorization function as expected
- Image storage and processing complete successfully
- Your implementation is ready for production use

If any test fails, refer to [LAB04-TROUBLESHOOTING.md](LAB04-TROUBLESHOOTING.md) for detailed debugging guidance.
