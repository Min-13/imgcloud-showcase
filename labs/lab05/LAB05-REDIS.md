# Lab 05 - Redis Caching Guide

This guide covers Redis caching implementation for Lab 05. Redis is used to cache database query results to reduce database load and improve response times.

## What is Redis?

Redis is an in-memory key-value store that provides fast read/write operations. It's commonly used for:
- Caching expensive database queries
- Session storage
- Rate limiting
- Real-time analytics

## Redis Data Model

Redis stores data as key-value pairs:
- **Keys**: Strings that identify the data (e.g., `"admin:users"`, `"query:images:abc123"`)
- **Values**: Strings (often JSON-encoded objects)
- **TTL**: Time-to-live in seconds (automatic expiration)

## Caching Pattern

The standard cache-aside pattern used in this lab:

```
1. Check cache for key
   ├─ If found (cache hit):
   │  └─ Return cached data immediately
   └─ If not found (cache miss):
      ├─ Query database
      ├─ Store result in cache with TTL
      └─ Return data
```

## Cache Keys

### Naming Convention

Use descriptive, hierarchical keys:

```
admin:users              # All users list
admin:images             # All images list
admin:operations         # Operations statistics
admin:jobs               # Job queue status
```

For parameterized queries, include a hash:

```
query:user_images:5c3a1b  # Images for specific user (hash of user_id)
query:search:7f9e2d       # Search results (hash of search params)
```

### Key Generation

**Python:**
```python
import hashlib
import json

def generate_cache_key(prefix, params=None):
    if params is None:
        return f"admin:{prefix}"
    
    # Create hash from parameters (using SHA-256 for better practice)
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]  # First 16 chars
    return f"query:{prefix}:{param_hash}"

# Examples
key1 = generate_cache_key("users")  # "admin:users"
key2 = generate_cache_key("user_images", {"user_id": 123})  # "query:user_images:5c3a1b..."
```

**PHP:**
```php
function generateCacheKey($prefix, $params = null) {
    if ($params === null) {
        return "admin:{$prefix}";
    }
    
    ksort($params);
    $paramStr = json_encode($params);
    $paramHash = substr(hash('sha256', $paramStr), 0, 16);  // First 16 chars of SHA-256
    return "query:{$prefix}:{$paramHash}";
}
```

**C++:**
```cpp
#include <sstream>
#include <iomanip>
#include <openssl/sha.h>  // For SHA-256

std::string generateCacheKey(const std::string& prefix) {
    return "admin:" + prefix;
}

std::string generateCacheKey(const std::string& prefix, const json& params) {
    std::string param_str = params.dump();
    
    // Use SHA-256 for better hash quality
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256((unsigned char*)param_str.c_str(), param_str.length(), hash);
    
    // Convert first 8 bytes to hex string
    std::stringstream ss;
    for (int i = 0; i < 8; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    
    return "query:" + prefix + ":" + ss.str();
}
```

## Time-to-Live (TTL)

TTL determines how long cached data remains valid:

### Recommended TTLs

| Data Type | TTL | Reasoning |
|-----------|-----|-----------|
| Users list | 300s (5 min) | Changes infrequently |
| Images list | 300s (5 min) | Changes infrequently |
| Operations stats | 300s (5 min) | Statistical data |
| Job queue status | 60s (1 min) | Changes frequently |
| User-specific data | 180s (3 min) | Medium frequency |

### Setting TTL

**Python (redis-py):**
```python
# Set with TTL
cache.set("admin:users", json.dumps(data), 300)  # 300 seconds

# Or using setex
redis_client.setex("admin:users", 300, json.dumps(data))
```

**PHP (phpredis):**
```php
// Set with TTL
$redis->setex("admin:users", 300, json_encode($data));  // 300 seconds
```

**C++ (hiredis):**
```cpp
// Set with TTL using SETEX
redisReply* reply = (redisReply*)redisCommand(
    redis_ctx,
    "SETEX %s %d %s",
    key.c_str(),
    300,  // TTL in seconds
    value.c_str()
);
freeReplyObject(reply);
```

## Cache Operations

### GET - Retrieve from Cache

**Python:**
```python
value = cache.get("admin:users")
if value:
    # Cache hit
    data = json.loads(value)
    return data
else:
    # Cache miss - query database
    pass
```

**PHP:**
```php
$value = $redis->get("admin:users");
if ($value !== false) {
    // Cache hit
    $data = json_decode($value, true);
    return $data;
} else {
    // Cache miss - query database
}
```

**C++:**
```cpp
redisReply* reply = (redisReply*)redisCommand(redis_ctx, "GET %s", "admin:users");
if (reply->type == REDIS_REPLY_STRING) {
    // Cache hit
    std::string value(reply->str, reply->len);
    json data = json::parse(value);
    freeReplyObject(reply);
    return data;
}
freeReplyObject(reply);
// Cache miss - query database
```

### SET - Store in Cache

**Python:**
```python
# Store with 5-minute TTL
cache.set("admin:users", json.dumps(data), 300)
```

**PHP:**
```php
// Store with 5-minute TTL
$redis->setex("admin:users", 300, json_encode($data));
```

**C++:**
```cpp
// Store with 5-minute TTL
std::string json_str = data.dump();
redisReply* reply = (redisReply*)redisCommand(
    redis_ctx,
    "SETEX %s %d %s",
    "admin:users",
    300,
    json_str.c_str()
);
freeReplyObject(reply);
```

### DELETE - Invalidate Cache

Use when data changes (e.g., after INSERT/UPDATE/DELETE):

**Python:**
```python
cache.delete("admin:users")
```

**PHP:**
```php
$redis->del("admin:users");
```

**C++:**
```cpp
redisReply* reply = (redisReply*)redisCommand(redis_ctx, "DEL %s", "admin:users");
freeReplyObject(reply);
```

## Complete Caching Example

### Python

```python
@app.route('/api/users')
def get_users():
    # 1. Check cache
    cache_key = "admin:users"
    cached = cache.get(cache_key)
    
    if cached:
        # Cache hit
        data = json.loads(cached)
        return jsonify({"users": data, "cached": True, "cache_ttl": 300})
    
    # 2. Cache miss - query database
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT u.id, u.username, u.email,
                   COUNT(DISTINCT i.id) as image_count,
                   COUNT(DISTINCT j.id) as job_count
            FROM users u
            LEFT JOIN images i ON u.id = i.user_id
            LEFT JOIN jobs j ON u.id = j.user_id
            GROUP BY u.id, u.username, u.email
            ORDER BY u.id
        """)
        rows = cursor.fetchall()
    
    # 3. Format results
    users = [{"id": r[0], "username": r[1], "email": r[2],
              "image_count": r[3], "job_count": r[4]} for r in rows]
    
    # 4. Store in cache
    cache.set(cache_key, json.dumps(users), 300)
    
    # 5. Return with cache metadata
    return jsonify({"users": users, "cached": False, "cache_ttl": 300})
```

### PHP

```php
<?php
require_once 'db.php';
require_once 'cache.php';

header('Content-Type: application/json');

// 1. Check cache
$cache = CacheManager::getInstance();
$cache_key = "admin:users";
$cached = $cache->get($cache_key);

if ($cached !== null) {
    // Cache hit
    echo $cached;
    exit;
}

// 2. Cache miss - query database
$db = Database::getInstance();
$pdo = $db->getConnection();

$stmt = $pdo->query("
    SELECT DISTINCT u.id, u.username, u.email,
           COUNT(DISTINCT i.id) as image_count,
           COUNT(DISTINCT j.id) as job_count
    FROM users u
    LEFT JOIN images i ON u.id = i.user_id
    LEFT JOIN jobs j ON u.id = j.user_id
    GROUP BY u.id, u.username, u.email
    ORDER BY u.id
");

$users = $stmt->fetchAll(PDO::FETCH_ASSOC);

// 3. Format response
$response = [
    'users' => $users,
    'cached' => false,
    'cache_ttl' => 300
];

// 4. Store in cache
$json_response = json_encode($response);
$cache->set($cache_key, $json_response, 300);

// 5. Return
echo $json_response;
```

### C++

```cpp
json UsersEndpoint::handleRequest(DatabaseConnection& db, CacheConnection& cache) {
    // 1. Check cache
    std::string cache_key = "admin:users";
    auto cached_data = cache.get(cache_key);
    
    if (cached_data.has_value()) {
        // Cache hit
        json response = cached_data.value();
        response["cached"] = true;
        return response;
    }
    
    // 2. Cache miss - query database
    std::string query = R"(
        SELECT DISTINCT u.id, u.username, u.email,
               COUNT(DISTINCT i.id) as image_count,
               COUNT(DISTINCT j.id) as job_count
        FROM users u
        LEFT JOIN images i ON u.id = i.user_id
        LEFT JOIN jobs j ON u.id = j.user_id
        GROUP BY u.id, u.username, u.email
        ORDER BY u.id
    )";
    
    auto results = db.executeQuery(query);
    
    // 3. Convert to JSON
    json users_json = json::array();
    for (const auto& row : results) {
        json user;
        user["id"] = row.at("id");
        user["username"] = row.at("username");
        user["email"] = row.at("email");
        user["image_count"] = row.at("image_count");
        user["job_count"] = row.at("job_count");
        users_json.push_back(user);
    }
    
    // 4. Format response
    json response = {
        {"users", users_json},
        {"cached", false},
        {"cache_ttl", 300}
    };
    
    // 5. Store in cache and return
    cache.set(cache_key, response, 300);
    return response;
}
```

## Testing Redis

### Test Connection

**Python:**
```python
import redis
import os

def test_redis_connection():
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test PING
        if r.ping():
            print("✓ Redis connection successful")
        
        # Test SET/GET
        r.set("test_key", "test_value", ex=10)
        value = r.get("test_key")
        if value == "test_value":
            print("✓ Redis GET/SET working")
        
        # Test DEL
        r.delete("test_key")
        if r.get("test_key") is None:
            print("✓ Redis DEL working")
        
        return True
    except Exception as e:
        print(f"✗ Redis error: {e}")
        return False

test_redis_connection()
```

**PHP:**
```php
<?php

function testRedisConnection() {
    try {
        $redis_url = getenv('REDIS_URL') ?: 'redis://redis:6379';
        $parsed = parse_url($redis_url);
        
        $redis = new Redis();
        $redis->connect($parsed['host'], $parsed['port'] ?? 6379);
        
        // Test PING
        if ($redis->ping() === '+PONG') {
            echo "✓ Redis connection successful\n";
        }
        
        // Test SET/GET
        $redis->setex('test_key', 10, 'test_value');
        if ($redis->get('test_key') === 'test_value') {
            echo "✓ Redis GET/SET working\n";
        }
        
        // Test DEL
        $redis->del('test_key');
        if ($redis->get('test_key') === false) {
            echo "✓ Redis DEL working\n";
        }
        
        return true;
    } catch (Exception $e) {
        echo "✗ Redis error: " . $e->getMessage() . "\n";
        return false;
    }
}

testRedisConnection();
```

**C++:**
```cpp
#include <hiredis/hiredis.h>
#include <iostream>

bool testRedisConnection() {
    const char* host = "redis";
    int port = 6379;
    
    // Connect
    redisContext* ctx = redisConnect(host, port);
    if (ctx == nullptr || ctx->err) {
        std::cerr << "✗ Redis connection failed\n";
        if (ctx) redisFree(ctx);
        return false;
    }
    std::cout << "✓ Redis connection successful\n";
    
    // Test PING
    redisReply* reply = (redisReply*)redisCommand(ctx, "PING");
    if (reply && reply->type == REDIS_REPLY_STATUS) {
        std::cout << "✓ Redis PING successful\n";
    }
    freeReplyObject(reply);
    
    // Test SET/GET
    reply = (redisReply*)redisCommand(ctx, "SETEX test_key 10 test_value");
    freeReplyObject(reply);
    
    reply = (redisReply*)redisCommand(ctx, "GET test_key");
    if (reply && reply->type == REDIS_REPLY_STRING) {
        std::string value(reply->str, reply->len);
        if (value == "test_value") {
            std::cout << "✓ Redis GET/SET working\n";
        }
    }
    freeReplyObject(reply);
    
    // Test DEL
    reply = (redisReply*)redisCommand(ctx, "DEL test_key");
    freeReplyObject(reply);
    
    redisFree(ctx);
    return true;
}
```

### Test Cache Hit/Miss

```bash
# First request (cache miss)
time curl http://localhost:YOUR_PORT/api/users

# Second request (cache hit - should be faster)
time curl http://localhost:YOUR_PORT/api/users

# Check response - cached should be true on second request
```

### View Cache Contents (Redis CLI)

```bash
# Connect to Redis container
docker exec -it <redis-container> redis-cli

# List all keys
KEYS *

# Get specific key
GET admin:users

# Check TTL (time remaining)
TTL admin:users

# Delete key
DEL admin:users

# Monitor commands in real-time
MONITOR

# Exit
quit
```

### Verify Caching is Working

```bash
# 1. Clear all cache
docker exec -it <redis-container> redis-cli FLUSHALL

# 2. Make request - should be slow (database query)
time curl http://localhost:YOUR_PORT/api/users
# Response should show: "cached": false

# 3. Make same request - should be fast (from cache)
time curl http://localhost:YOUR_PORT/api/users
# Response should show: "cached": true

# 4. Check cache key exists
docker exec -it <redis-container> redis-cli EXISTS admin:users
# Should return: (integer) 1

# 5. Wait for TTL to expire (or delete manually)
# After 300 seconds, key should be gone
docker exec -it <redis-container> redis-cli TTL admin:users
# Returns: (integer) -2 when expired
```

## Common Issues

### Connection Refused
```
Error: Connection refused (Redis)
```
**Solution:** Check Docker network and Redis container is running:
```bash
docker ps | grep redis
docker logs <redis-container>
```

### Authentication Error
```
Error: NOAUTH Authentication required
```
**Solution:** Add password to REDIS_URL:
```
REDIS_URL=redis://:password@redis:6379/0
```

### Serialization Error
```
Error: Cannot cache complex objects
```
**Solution:** Convert objects to JSON strings before caching:
```python
# Wrong
cache.set("key", {"data": [1, 2, 3]})

# Correct
cache.set("key", json.dumps({"data": [1, 2, 3]}))
```

### Cache Never Expires
```
Keys stay in Redis forever
```
**Solution:** Always use SETEX (set with expiry), not SET:
```python
# Wrong
redis.set("key", "value")

# Correct
redis.setex("key", 300, "value")  # Expires in 300 seconds
```

## Best Practices

1. **Always set TTL** - Prevents stale data and memory issues
2. **Use consistent keys** - Makes debugging and monitoring easier
3. **Handle cache failures gracefully** - Application should work even if Redis is down
4. **Invalidate on writes** - Delete cache keys when data changes
5. **Monitor cache hit rate** - Aim for >70% hit rate for frequently accessed data
6. **Use appropriate TTLs** - Balance freshness vs. performance

## Performance Benefits

With proper caching:
- **Response time**: 100ms → 5ms (20x faster)
- **Database load**: Reduced by 70-90%
- **Concurrent users**: 10x more capacity
- **Cost**: Lower database hosting costs

## References

- [Redis Commands](https://redis.io/commands)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Cache-Aside Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)
- [LAB05.md](LAB05.md) - Main lab requirements
- [LAB05-TROUBLESHOOTING.md](LAB05-TROUBLESHOOTING.md) - Debugging guide
