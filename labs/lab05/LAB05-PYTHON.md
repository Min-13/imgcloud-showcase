# Lab 05 - Python Implementation Guide

This guide provides Python-specific implementation details for Lab 05. Refer to [LAB05.md](LAB05.md) for requirements and [LAB05-QUERIES.md](LAB05-QUERIES.md) for query examples.

## File Structure

Create these files in your `imgprocessor/` directory:

```
imgprocessor/
├── db.py           # Database connection management
├── cache.py        # Redis cache implementation
└── endpoints.py    # Query endpoint implementations (or separate files per query)
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## Required Libraries

Install via pip (add to requirements.txt):

```txt
psycopg2-binary>=2.9.0
redis>=4.0.0
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## Database Connection (`db.py`)

### URL Parsing

Place this in your `db.py` file to parse DATABASE_URL:

```python
# db.py
from urllib.parse import urlparse
import os

db_url = os.environ.get('DATABASE_URL')
parsed = urlparse(db_url)

# Extract components
hostname = parsed.hostname
port = parsed.port
database = parsed.path[1:]  # Remove leading '/'
username = parsed.username
password = parsed.password
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Connection Pool Setup

Use `psycopg2.pool.ThreadedConnectionPool`:

```python
from psycopg2 import pool

class DatabasePool:
    def __init__(self):
        # Parse DATABASE_URL here
        self.connection_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=hostname,
            port=port,
            database=database,
            user=username,
            password=password
        )
    
    def get_connection(self):
        return self.connection_pool.getconn()
    
    def return_connection(self, conn):
        self.connection_pool.putconn(conn)
    
    def close_all(self):
        self.connection_pool.closeall()
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Using Connections

Always return connections to the pool:

```python
db_pool = DatabasePool()

# Get connection
conn = db_pool.get_connection()
try:
    cursor = conn.cursor()
    # Execute queries
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    cursor.close()
finally:
    db_pool.return_connection(conn)
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

Better pattern with context manager:

```python
from contextlib import contextmanager

@contextmanager
def get_db_cursor():
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        cursor.close()
    finally:
        db_pool.return_connection(conn)

# Usage
with get_db_cursor() as cursor:
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## Redis Cache (`cache.py`)

### Connection Setup

```python
import redis
import os

class CacheManager:
    def __init__(self):
        redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    def get(self, key):
        """Get value from cache"""
        return self.redis_client.get(key)
    
    def set(self, key, value, ttl=300):
        """Set value in cache with TTL in seconds"""
        return self.redis_client.setex(key, ttl, value)
    
    def delete(self, key):
        """Delete key from cache"""
        return self.redis_client.delete(key)
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Cache Key Generation

Use consistent key naming with hashing for complex queries:

```python
import hashlib
import json

def generate_cache_key(query_name, params):
    """Generate consistent cache key"""
    # Create unique string from parameters
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    return f"query:{query_name}:{param_hash}"
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## Parameterized Queries for SQL Injection Prevention

### Why Parameterized Queries?

**Never** build SQL queries with string concatenation or formatting:

```python
# ❌ DANGEROUS - SQL Injection Vulnerable
user_id = request.args.get('user_id')
query = f"SELECT * FROM users WHERE id = {user_id}"  # NEVER DO THIS!
cursor.execute(query)

# ❌ ALSO DANGEROUS
query = "SELECT * FROM users WHERE id = " + user_id  # NEVER DO THIS!
cursor.execute(query)

# ❌ STILL DANGEROUS
query = "SELECT * FROM users WHERE id = %s" % (user_id,)  # NEVER DO THIS!
cursor.execute(query)
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

**Why it's dangerous:** Attacker can inject SQL:
```python
user_id = "1 OR 1=1; DROP TABLE users; --"
# Results in: SELECT * FROM users WHERE id = 1 OR 1=1; DROP TABLE users; --
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Using %s Placeholders Safely

Python/psycopg2 uses `%s` for **all types** (integers, strings, dates, etc.):

```python
# ✅ SAFE - Single parameter
user_id = request.args.get('user_id', type=int)
cursor.execute(
    "SELECT * FROM users WHERE id = %s",
    (user_id,)  # Note: comma for single-item tuple
)

# ✅ SAFE - Multiple parameters
cursor.execute(
    "SELECT * FROM images WHERE user_id = %s AND created_at > %s",
    (user_id, date_threshold)
)

# ✅ SAFE - String parameters (automatically escaped)
username = request.args.get('username')
cursor.execute(
    "SELECT * FROM users WHERE username = %s",
    (username,)  # psycopg2 automatically escapes quotes and special chars
)

# ✅ SAFE - IN clause with list
ids = [1, 2, 3, 4]
cursor.execute(
    "SELECT * FROM images WHERE id = ANY(%s)",
    (ids,)  # psycopg2 handles arrays properly
)
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### How Parameterized Queries Work

psycopg2 sends the query and parameters **separately** to PostgreSQL:

1. Query template sent: `SELECT * FROM users WHERE id = $1`
2. Parameters sent separately: `[123]`
3. PostgreSQL treats parameters as **data**, never as SQL code
4. Result: SQL injection is **impossible**

### Additional Safety Tips

```python
# Always validate input types
user_id = request.args.get('user_id', type=int)
if user_id is None:
    return jsonify({"error": "Invalid user_id"}), 400

# Use type conversion for safety
limit = int(request.args.get('limit', 50))
cursor.execute("SELECT * FROM images LIMIT %s", (limit,))

# For dynamic column names (can't be parameterized), use whitelisting
allowed_columns = {'id', 'username', 'email', 'created_at'}
sort_by = request.args.get('sort_by', 'id')
if sort_by not in allowed_columns:
    sort_by = 'id'
# Now safe to use in query
cursor.execute(f"SELECT * FROM users ORDER BY {sort_by}")  # OK because whitelisted
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Fetching Results

```python
# Fetch all rows
cursor.execute("SELECT id, username FROM users")
rows = cursor.fetchall()  # List of tuples: [(1, 'alice'), (2, 'bob')]

# Fetch one row
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
row = cursor.fetchone()  # Single tuple or None

# With column names (using DictCursor)
from psycopg2.extras import DictCursor

cursor = conn.cursor(cursor_factory=DictCursor)
cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
row = cursor.fetchone()
# Access as: row['id'], row['username']
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## Query Endpoint Pattern

### Basic Structure

```python
from flask import Flask, jsonify, request
import json

app = Flask(__name__)
cache = CacheManager()
db = DatabasePool()

@app.route('/api/query1')
def query1_endpoint():
    # 1. Extract parameters from request
    user_id = request.args.get('user_id', type=int)
    
    if user_id is None:
        return jsonify({"error": "user_id required"}), 400
    
    # 2. Generate cache key
    cache_key = generate_cache_key('query1', {'user_id': user_id})
    
    # 3. Check cache
    cached = cache.get(cache_key)
    if cached:
        return jsonify(json.loads(cached))
    
    # 4. Execute query
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT column1, column2
            FROM table_name
            WHERE user_id = %s
        """, (user_id,))
        
        rows = cursor.fetchall()
    
    # 5. Format response
    result = {
        "data": [{"column1": row[0], "column2": row[1]} for row in rows]
    }
    
    # 6. Cache result
    cache.set(cache_key, json.dumps(result), ttl=300)
    
    # 7. Return response
    return jsonify(result)
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Handling JSON Aggregation

When SQL returns JSON (from json_agg):

```python
cursor.execute("""
    SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
    FROM (
        SELECT id, username, email
        FROM users
        WHERE created_at > %s
    ) t
""", (date_threshold,))

json_result = cursor.fetchone()[0]
# json_result is already a Python object (list/dict)

return jsonify({"users": json_result})
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Error Handling

```python
from psycopg2 import Error as PGError

@app.route('/api/query2')
def query2_endpoint():
    try:
        # Query logic here
        pass
    except PGError as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## Complete Endpoint Example Pattern

```python
@app.route('/api/user_images')
def user_images():
    """Get all images for a user with metadata"""
    # Validate input
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    # Check cache
    cache_key = f"query:user_images:{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(json.loads(cached))
    
    # Query database
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    i.id,
                    i.filename,
                    i.size,
                    i.created_at,
                    COUNT(t.id) as tag_count
                FROM images i
                LEFT JOIN image_tags it ON i.id = it.image_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.user_id = %s
                GROUP BY i.id
                ORDER BY i.created_at DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            
            # Format results
            images = []
            for row in rows:
                images.append({
                    "id": row[0],
                    "filename": row[1],
                    "size": row[2],
                    "created_at": row[3].isoformat() if row[3] else None,
                    "tag_count": row[4]
                })
            
            result = {"images": images}
            
            # Cache and return
            cache.set(cache_key, json.dumps(result), ttl=300)
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## Testing Tips

### Test Database Connection

```python
def test_connection():
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"Connected to: {version}")
        cursor.close()
        db_pool.return_connection(conn)
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Test Redis Connection

```python
def test_redis():
    try:
        cache.set("test_key", "test_value", ttl=10)
        value = cache.get("test_key")
        assert value == "test_value"
        cache.delete("test_key")
        print("Redis connection OK")
        return True
    except Exception as e:
        print(f"Redis failed: {e}")
        return False
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Manual Query Testing

Use psql to test queries first:

```bash
docker exec -it <imgprocessor-container> bash
psql -h postgres -U imgcloud -d imgcloud

# Test your queries
SELECT * FROM users LIMIT 5;
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## Common Patterns

### Optional Parameters

```python
@app.route('/api/search_images')
def search_images():
    user_id = request.args.get('user_id', type=int)
    tag = request.args.get('tag')
    limit = request.args.get('limit', default=50, type=int)
    
    query = "SELECT * FROM images WHERE 1=1"
    params = []
    
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    
    if tag:
        query += " AND EXISTS (SELECT 1 FROM image_tags it JOIN tags t ON it.tag_id = t.id WHERE it.image_id = images.id AND t.name = %s)"
        params.append(tag)
    
    query += " LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, tuple(params))
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

### Pagination

```python
page = request.args.get('page', default=1, type=int)
per_page = request.args.get('per_page', default=20, type=int)

offset = (page - 1) * per_page

cursor.execute("""
    SELECT * FROM images
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s
""", (per_page, offset))
```

For more complex parsing patterns or validation, see [LAB05-REGEX.md](LAB05-REGEX.md).

## References

- [psycopg2 documentation](https://www.psycopg.org/docs/)
- [redis-py documentation](https://redis-py.readthedocs.io/)
- [Flask documentation](https://flask.palletsprojects.com/)
- [LAB05.md](LAB05.md) - Main lab requirements
- [LAB05-QUERIES.md](LAB05-QUERIES.md) - Query examples
- [LAB05-REDIS.md](LAB05-REDIS.md) - Redis caching guide and testing
- [LAB05-TROUBLESHOOTING.md](LAB05-TROUBLESHOOTING.md) - Common issues
