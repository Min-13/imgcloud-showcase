# LAB04 - MinIO Object Storage

This document provides detailed information about using MinIO for object storage in LAB04.

## What is MinIO?

MinIO is a high-performance, S3-compatible object storage system. It's open-source, cloud-native, and designed for modern application infrastructure.

**Key Features:**
- **S3 Compatible**: Uses the same API as Amazon S3
- **High Performance**: Written in Go for speed and efficiency
- **Distributed**: Scales horizontally across multiple servers
- **Simple**: Easy to deploy and manage with Docker
- **Production Ready**: Used by major companies worldwide

## Why Object Storage?

Traditional file systems are not optimal for cloud applications:

| Feature | Filesystem | Object Storage |
|---------|-----------|----------------|
| Scalability | Limited by disk size | Scales to petabytes |
| Redundancy | Requires RAID/backup | Built-in replication |
| Metadata | Limited attributes | Rich custom metadata |
| Access Control | File permissions | Bucket policies |
| API Access | Mount required | HTTP REST API |
| Distribution | Single machine | Multi-server clusters |

## MinIO Concepts

### Buckets

Buckets are top-level containers for objects (similar to S3 buckets or Azure containers):

```python
# Create a bucket
minio_client.make_bucket("images")

# List all buckets
buckets = minio_client.list_buckets()

# Check if bucket exists
if not minio_client.bucket_exists("images"):
    minio_client.make_bucket("images")
```

**Bucket Naming Rules:**
- 3-63 characters long
- Lowercase letters, numbers, hyphens only
- Must start with letter or number
- Globally unique (in production S3)

### Objects

Objects are individual files stored in buckets:

```python
# Upload an object
minio_client.put_object(
    bucket_name="images",
    object_name="users/alice/photo.jpg",
    data=io.BytesIO(image_data),
    length=len(image_data),
    content_type="image/jpeg"
)

# Download an object
response = minio_client.get_object("images", "users/alice/photo.jpg")
image_data = response.read()

# Delete an object
minio_client.remove_object("images", "users/alice/photo.jpg")
```

### Object Keys

Object keys are unique identifiers within a bucket (like file paths):

```
images/                          # Bucket
  users/                         # Logical "folder"
    123/                         # User ID
      original_456.jpg           # Original upload
      processed_789.jpg          # Processed result
      thumbnail_456_small.jpg    # Small thumbnail
      thumbnail_456_medium.jpg   # Medium thumbnail
```

**Best Practices:**
- Use forward slashes for hierarchy
- Include identifiers (user_id, image_id) for organization
- Use consistent naming conventions
- Avoid special characters

## Python MinIO Client

### Installation

Already included in `requirements.txt`:
```
minio==7.2.0
```

### Configuration

```python
from minio import Minio

# Initialize MinIO client
minio_client = Minio(
    endpoint="minio:9000",  # Service name in Docker network
    access_key="minioadmin",
    secret_key="minioadmin123",
    secure=False  # Use HTTPS in production
)
```

### Common Operations

#### Upload Image

```python
def upload_image(user_id, image_id, image_data, content_type):
    """Upload an image to MinIO"""
    object_name = f"users/{user_id}/original_{image_id}.jpg"
    
    minio_client.put_object(
        bucket_name="images",
        object_name=object_name,
        data=io.BytesIO(image_data),
        length=len(image_data),
        content_type=content_type,
        metadata={
            "user-id": str(user_id),
            "image-id": str(image_id),
            "upload-time": datetime.utcnow().isoformat()
        }
    )
    
    return object_name
```

#### Download Image

```python
def download_image(object_name):
    """Download an image from MinIO"""
    try:
        response = minio_client.get_object("images", object_name)
        image_data = response.read()
        return image_data
    finally:
        response.close()
        response.release_conn()
```

#### Generate Presigned URL

For temporary direct download links (useful for sharing):

```python
def get_download_url(object_name, expires_hours=1):
    """Generate a temporary download URL"""
    url = minio_client.presigned_get_object(
        bucket_name="images",
        object_name=object_name,
        expires=timedelta(hours=expires_hours)
    )
    return url
```

#### List User's Images

```python
def list_user_images(user_id):
    """List all images for a user"""
    prefix = f"users/{user_id}/"
    objects = minio_client.list_objects(
        bucket_name="images",
        prefix=prefix,
        recursive=True
    )
    
    return [obj.object_name for obj in objects]
```

#### Delete Image

```python
def delete_image(object_name):
    """Delete an image from MinIO"""
    minio_client.remove_object("images", object_name)
```

## Error Handling

```python
from minio.error import S3Error

try:
    minio_client.put_object(...)
except S3Error as err:
    if err.code == "NoSuchBucket":
        # Bucket doesn't exist, create it
        minio_client.make_bucket("images")
        minio_client.put_object(...)
    elif err.code == "AccessDenied":
        # Permission issue
        print("Access denied to bucket")
    else:
        # Other S3 errors
        print(f"S3 Error: {err}")
except Exception as err:
    # Network or other errors
    print(f"Error: {err}")
```

## Data Organization Strategy

### Folder Structure

```
images/                                    # Bucket
  users/{user_id}/                         # Per-user folder
    originals/{image_id}.jpg               # Original uploads
    processed/{job_id}.jpg                 # Processed results
    thumbnails/{image_id}_small.jpg        # Small thumbnails
    thumbnails/{image_id}_medium.jpg       # Medium thumbnails
```

**Benefits:**
- Easy to find user's files
- Logical separation of file types
- Simple cleanup (delete entire user folder)
- Clear naming convention

### Metadata Strategy

Store metadata in both MinIO and PostgreSQL:

**MinIO Metadata** (with the object):
- Original filename
- Content type
- Upload timestamp
- User ID

**PostgreSQL Metadata** (in database):
- User relationships
- Image descriptions
- Tags and categories
- Processing history
- Access counts

**Why both?**
- MinIO: Fast access when downloading files
- PostgreSQL: Complex queries and relationships

## Performance Tips

### 1. Use Multipart Upload for Large Files

For files larger than 5MB:

```python
from minio import Minio

# MinIO automatically uses multipart for files > 5MB
minio_client.put_object(
    bucket_name="images",
    object_name="large_photo.jpg",
    data=large_file,
    length=len(large_file)
)
```

### 2. Stream Instead of Loading Entire File

```python
# Bad - loads entire file into memory
with open("large_image.jpg", "rb") as f:
    data = f.read()
    minio_client.put_object(..., data=io.BytesIO(data), ...)

# Good - streams file directly
with open("large_image.jpg", "rb") as f:
    minio_client.put_object(..., data=f, length=os.path.getsize("large_image.jpg"))
```

### 3. Use Connection Pooling

The MinIO client automatically pools connections. Create one client instance and reuse it:

```python
# Good - single instance
minio_client = Minio(...)

def upload_image():
    minio_client.put_object(...)

# Bad - creates new connection each time
def upload_image():
    client = Minio(...)  # Don't do this
    client.put_object(...)
```

## Security Considerations

### Access Keys

In production:
- Use strong, random access keys
- Rotate keys regularly
- Use environment variables (never hardcode)
- Apply principle of least privilege

```python
# Good
access_key = os.environ.get('MINIO_ACCESS_KEY')
secret_key = os.environ.get('MINIO_SECRET_KEY')

# Bad
access_key = "minioadmin"  # Don't hardcode
```

### Bucket Policies

Control who can access buckets:

```python
from minio import Minio
import json

policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::images/public/*"]
        }
    ]
}

minio_client.set_bucket_policy("images", json.dumps(policy))
```

### HTTPS in Production

Always use HTTPS in production:

```python
minio_client = Minio(
    endpoint="minio.example.com",
    access_key=access_key,
    secret_key=secret_key,
    secure=True  # HTTPS
)
```

## Testing MinIO Operations

### Unit Tests with Mocking

```python
from unittest.mock import MagicMock, patch

def test_upload_image():
    # Mock MinIO client
    mock_client = MagicMock()
    
    # Test upload
    upload_image(
        user_id=123,
        image_id=456,
        image_data=b"fake image data",
        content_type="image/jpeg"
    )
    
    # Verify called correctly
    mock_client.put_object.assert_called_once()
```

### Integration Tests with Docker

```bash
# Start MinIO for testing
docker run -d -p 9000:9000 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin123 \
  minio/minio server /data

# Run tests
python -m pytest tests/

# Cleanup
docker stop minio-test
```

## Monitoring and Debugging

### Check Bucket Contents

```python
# List all objects in bucket
objects = minio_client.list_objects("images", recursive=True)
for obj in objects:
    print(f"{obj.object_name} - {obj.size} bytes")
```

### Get Object Info

```python
# Get metadata about an object
stat = minio_client.stat_object("images", "users/123/photo.jpg")
print(f"Size: {stat.size}")
print(f"Content-Type: {stat.content_type}")
print(f"Last Modified: {stat.last_modified}")
print(f"Metadata: {stat.metadata}")
```

### Check MinIO Health

```python
# Check if MinIO is accessible
try:
    buckets = minio_client.list_buckets()
    print("MinIO is healthy")
except Exception as e:
    print(f"MinIO is not accessible: {e}")
```

## Common Issues

### Issue: "Bucket does not exist"

**Solution:** Create the bucket on application startup:

```python
if not minio_client.bucket_exists("images"):
    minio_client.make_bucket("images")
```

### Issue: "Connection refused"

**Solution:** Check:
- MinIO container is running
- Correct hostname (use service name in Docker network)
- Correct port (9000 for API, 9001 for console)
- Services on same Docker network

### Issue: "Access denied"

**Solution:** Check:
- Access key and secret key are correct
- Bucket policy allows the operation
- Object name doesn't have special characters

### Issue: "Object too large"

**Solution:** MinIO supports files up to 5TB by default. If hitting limits:
- Check disk space on MinIO container
- Check volume mount is correct
- Verify network can handle large transfers

## Summary

MinIO provides:
- ✅ S3-compatible API for cloud storage
- ✅ High performance for large binary files
- ✅ Easy integration with Python
- ✅ Scalable architecture
- ✅ Production-ready reliability

For more details, see the [MinIO Python SDK documentation](https://min.io/docs/minio/linux/developers/python/minio-py.html).
