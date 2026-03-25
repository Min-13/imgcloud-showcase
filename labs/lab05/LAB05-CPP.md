# Lab 05 - C++ Implementation Guide

This guide provides C++-specific implementation details for Lab 05. Refer to [LAB05.md](LAB05.md) for requirements and [LAB05-QUERIES.md](LAB05-QUERIES.md) for query examples.

## Overview

The admin interface framework is provided in `admin/cpp/`. You need to complete three modules:
- `db.cpp` - Database connection pooling
- `cache.cpp` - Redis caching  
- `endpoints.cpp` - SQL queries for Users and Images endpoints

The HTTP server, routing, and two example endpoints (Operations and Jobs) are already implemented.

## Required Libraries

All required libraries are already configured in the Makefile and Dockerfile:
- `libpqxx` - PostgreSQL C++ client
- `hiredis` - Redis C++ client
- `nlohmann/json` - JSON library

You do not need to modify the Makefile or Dockerfile.

## Database Connection (`db.cpp`)

### Tasks

1. **Parse DATABASE_URL** from environment variable
   - Format: `postgresql://user:password@host:port/database`
   - Extract host, port, database name, username, password
   
2. **Create connection pool**
   - Use `pqxx::connection_pool` with 10 connections
   - Store in the `pool` member variable

3. **Execute parameterized queries**
   - Get connection from pool using `pool->claim()`
   - Create transaction with `pqxx::work`
   - Use `exec_params()` for queries with parameters
   - Convert results to vector of maps
   - Connection automatically returned when out of scope

### Parameterized Queries for SQL Injection Prevention

**Never** build SQL queries with string concatenation:

```cpp
// ❌ DANGEROUS - SQL Injection Vulnerable
std::string user_id = getParam("user_id");
std::string query = "SELECT * FROM users WHERE id = " + user_id;  // NEVER DO THIS!
pqxx::result r = txn.exec(query);

// ❌ ALSO DANGEROUS
query = "SELECT * FROM users WHERE id = '" + username + "'";  // NEVER DO THIS!

// ❌ STILL DANGEROUS (stringstream)
std::stringstream ss;
ss << "SELECT * FROM users WHERE id = " << user_id;  // NEVER DO THIS!
```

**Why it's dangerous:** Attacker can inject SQL:
```cpp
user_id = "1 OR 1=1; DROP TABLE users; --";
// Results in: SELECT * FROM users WHERE id = 1 OR 1=1; DROP TABLE users; --
```

### Using exec_params() Safely

libpqxx uses `exec_params()` for parameterized queries:

```cpp
// ✅ SAFE - Single parameter
int user_id = 123;
pqxx::result r = txn.exec_params(
    "SELECT * FROM users WHERE id = $1",
    user_id
);

// ✅ SAFE - Multiple parameters
std::string username = "alice";
int min_age = 18;
pqxx::result r = txn.exec_params(
    "SELECT * FROM users WHERE username = $1 AND age >= $2",
    username,
    min_age
);

// ✅ SAFE - String parameters (automatically escaped)
std::string search_term = "O'Brien";  // Contains quote
pqxx::result r = txn.exec_params(
    "SELECT * FROM users WHERE username = $1",
    search_term  // libpqxx handles escaping automatically
);

// ✅ SAFE - Multiple types
int user_id = 123;
std::string status = "active";
std::string date = "2024-01-01";
pqxx::result r = txn.exec_params(
    "SELECT * FROM images WHERE user_id = $1 AND status = $2 AND created_at > $3",
    user_id,
    status,
    date
);
```

### Placeholder Numbering

Use `$1`, `$2`, `$3`, etc. for parameters:

```cpp
// ✅ Correct numbering
pqxx::result r = txn.exec_params(
    "SELECT * FROM images WHERE user_id = $1 AND width >= $2 AND height >= $3",
    user_id,  // $1
    width,    // $2
    height    // $3
);

// ❌ Wrong - don't use ? or %s
pqxx::result r = txn.exec_params(
    "SELECT * FROM images WHERE user_id = ?",  // Wrong placeholder!
    user_id
);
```

### How Parameterized Queries Work

libpqxx sends the query and parameters **separately** to PostgreSQL:

1. Query template sent: `SELECT * FROM users WHERE id = $1`
2. Parameters sent separately: `[123]`
3. PostgreSQL treats parameters as **data**, never as SQL code
4. Result: SQL injection is **impossible**

### Key libpqxx Functions

```cpp
// Manual connection pool pattern
std::vector<std::unique_ptr<pqxx::connection>> connections;
std::mutex pool_mutex;

// Initialize pool with connections
for (int i = 0; i < 3; ++i) {
    connections.push_back(std::make_unique<pqxx::connection>(connection_string));
}

// Get connection from pool (returns shared_ptr with custom deleter)
std::shared_ptr<pqxx::connection> getConnection() {
    // Lock, get from vector, return with deleter that returns to pool
}

// Execute query with parameters (SAFE)
auto conn = getConnection();
pqxx::work txn(*conn);
pqxx::result r = txn.exec_params(
    "SELECT * FROM users WHERE id = $1 AND status = $2",
    user_id,
    status
);
txn.commit();

// Access results
for (const auto& row : r) {
    std::string value = row["column_name"].c_str();
}
```

### Additional Safety Tips

```cpp
// Validate input types
int user_id;
try {
    user_id = std::stoi(user_id_str);
} catch (const std::exception& e) {
    // Handle invalid input
    return error_response("Invalid user_id");
}

// Use exec_params for ALL queries with user input
pqxx::result r = txn.exec_params(
    "SELECT * FROM images WHERE user_id = $1 LIMIT $2",
    user_id,
    limit
);

// For dynamic column names (can't be parameterized), use whitelisting
std::set<std::string> allowed_columns = {"id", "username", "email", "created_at"};
std::string sort_by = getParam("sort_by", "id");
if (allowed_columns.find(sort_by) == allowed_columns.end()) {
    sort_by = "id";
}
// Now safe to use in query
std::string query = "SELECT * FROM users ORDER BY " + sort_by;  // OK because whitelisted
pqxx::result r = txn.exec(query);
```

### Never Use exec() with User Input

```cpp
// ❌ NEVER use exec() with concatenated user input
std::string user_input = getUserInput();
pqxx::result r = txn.exec("SELECT * FROM users WHERE name = '" + user_input + "'");

// ✅ ALWAYS use exec_params() with user input
pqxx::result r = txn.exec_params("SELECT * FROM users WHERE name = $1", user_input);
```

## Redis Cache (`cache.cpp`)

### Tasks

1. **Parse REDIS_URL** from environment variable
   - Format: `redis://host:port/db`
   - Default: `redis://redis:6379/0`

2. **Connect to Redis**
   - Use `redisConnect(host, port)`
   - Check for errors in `redis_ctx->err`

3. **Implement cache operations**
   - GET: Use `redisCommand(redis_ctx, "GET %s", key.c_str())`
   - SET: Use `redisCommand(redis_ctx, "SETEX %s %d %s", key, ttl, value)`
   - DEL: Use `redisCommand(redis_ctx, "DEL %s", key)`
   - Always free reply with `freeReplyObject(reply)`

### Key hiredis Functions

```cpp
// Connect
redis_ctx = redisConnect(host.c_str(), port);

// Execute command
redisReply* reply = (redisReply*)redisCommand(redis_ctx, "GET %s", key);

// Check reply type
if (reply->type == REDIS_REPLY_STRING) {
    std::string value(reply->str, reply->len);
}

// Free reply
freeReplyObject(reply);
```

## Endpoints (`endpoints.cpp`)

### Your Tasks

Implement two endpoints:
1. **UsersEndpoint** - Get users with statistics
2. **ImagesEndpoint** - Get recent images

### Pattern to Follow

Study the provided **OperationsEndpoint** and **JobsEndpoint** implementations to understand the pattern:

1. Check cache first
2. If cached, add `cached=true` and return
3. If not cached:
   - Write SQL query (see LAB05-QUERIES.md)
   - Execute query using `db.executeQuery()`
   - Convert results to JSON
   - Store in cache
   - Return response

### Example Structure

```cpp
json UsersEndpoint::handleRequest(DatabaseConnection& db, CacheConnection& cache) {
    // 1. Check cache
    auto cached_data = cache.get("admin:users");
    if (cached_data.has_value()) {
        json response = cached_data.value();
        response["cached"] = true;
        return response;
    }
    
    // 2. Write your SQL query here (see LAB05-QUERIES.md)
    std::string query = R"(
        -- Your SQL query
    )";
    
    // 3. Execute query
    auto results = db.executeQuery(query);
    
    // 4. Convert to JSON
    json data_json = json::array();
    for (const auto& row : results) {
        json obj;
        for (const auto& [key, value] : row) {
            obj[key] = value;
        }
        data_json.push_back(obj);
    }
    
    // 5. Format response
    json response = {
        {"users", data_json},  // or "images" for ImagesEndpoint
        {"cached", false},
        {"cache_ttl", getCacheTTL()}
    };
    
    // 6. Cache and return
    cache.set("admin:users", response, getCacheTTL());
    return response;
}
```

## Testing

### Build and Run

```bash
cd admin/cpp
make
./admin_server
```

### Test Endpoints

```bash
# Health check
curl http://localhost:YOUR_PORT/health

# Test endpoints (will return "Not implemented" until you complete them)
curl http://localhost:YOUR_PORT/api/users
curl http://localhost:YOUR_PORT/api/images

# These are provided and should work:
curl http://localhost:YOUR_PORT/api/operations
curl http://localhost:YOUR_PORT/api/jobs
```

## Common Issues

- **Connection pool errors**: Make sure you're creating the pool correctly in `initializeConnection()`
- **Parameterized query errors**: Use `exec_params()` not `exec()` when you have parameters
- **Redis connection fails**: Check REDIS_URL format and that Redis is running
- **JSON parsing errors**: Make sure you're converting all row values to strings

## References

- [libpqxx documentation](https://libpqxx.readthedocs.io/)
- [hiredis GitHub](https://github.com/redis/hiredis)
- [LAB05.md](LAB05.md) - Main lab requirements
- [LAB05-QUERIES.md](LAB05-QUERIES.md) - SQL query requirements
- [LAB05-REDIS.md](LAB05-REDIS.md) - Redis caching guide and testing
- [LAB05-TROUBLESHOOTING.md](LAB05-TROUBLESHOOTING.md) - Debugging guide
