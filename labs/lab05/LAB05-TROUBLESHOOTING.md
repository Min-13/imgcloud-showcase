# Lab 05 - Troubleshooting Guide

This guide covers common issues you may encounter while implementing database connectivity and caching.

## Database Connection Issues

### Connection Refused
**Symptom**: `Connection refused` or `could not connect to server`

**Causes**:
- PostgreSQL container not running
- Wrong hostname (use `postgres` service name, not `localhost`)
- Wrong port (default: 5432)

**Solutions**:
```bash
# Check if postgres container is running
docker ps | grep postgres

# Check postgres logs
docker logs <postgres-container-id>

# Verify connection from your application container (admin-cpp, admin-python, or admin-php)
# Replace <admin-container> with your actual container name
docker exec -it <admin-container> bash
# Inside container, try connecting
psql -h postgres -U imgcloud -d imgcloud
```

### Authentication Failed
**Symptom**: `password authentication failed`

**Causes**:
- Incorrect credentials in DATABASE_URL
- Environment variables not loaded

**Solutions**:
- Verify DATABASE_URL format: `postgresql://user:password@host:port/database`
- Check environment variables: `docker exec <container> env | grep DATABASE`
- Ensure `.env` file is properly mounted in docker-compose.yml

### Pool Exhausted
**Symptom**: `connection pool exhausted` or timeout errors

**Causes**:
- Connections not being closed
- Pool size too small for load

**Solutions**:
- Always close/return connections after use
- Increase pool size (10-20 for development)
- Use `with` statements (Python) or try-finally blocks

## Redis Connection Issues

### Cannot Connect to Redis
**Symptom**: `Error connecting to Redis` or `Connection refused`

**Causes**:
- Redis container not running
- Wrong hostname (use `redis` service name)
- Wrong port (default: 6379)

**Solutions**:
```bash
# Check if redis container is running
docker ps | grep redis

# Test redis connection from your application container
docker exec -it <admin-container> bash
# Try redis-cli
redis-cli -h redis ping
```

### Redis Key Not Found
**Symptom**: Cache misses when you expect hits

**Causes**:
- Keys not being set correctly
- TTL expired
- Key naming inconsistencies

**Solutions**:
- Use consistent key naming (e.g., `query:<hash>` or `query_<hash>`)
- Check if TTL is reasonable (300 seconds = 5 minutes)
- Debug by checking Redis directly:
```bash
redis-cli -h redis
> KEYS *
> GET query:<some-hash>
> TTL query:<some-hash>
```

## SQL Query Errors

### Syntax Errors
**Symptom**: `syntax error at or near...`

**Causes**:
- Missing quotes around string literals
- Incorrect SQL keywords
- Using wrong placeholder syntax

**Solutions**:
- Python: Use `%s` placeholders: `SELECT * FROM users WHERE id = %s`
- PHP: Use `?` placeholders: `SELECT * FROM users WHERE id = ?`
- C++: Use `$1, $2` placeholders: `SELECT * FROM users WHERE id = $1`
- Test queries in psql first

### Parameter Mismatch
**Symptom**: `wrong number of parameters` or `bind variable does not exist`

**Causes**:
- Number of placeholders doesn't match number of parameters
- Wrong parameter passing format

**Solutions**:
- Count placeholders and ensure equal number of parameters
- Python: Pass as tuple: `cursor.execute(query, (param1, param2))`
- PHP: Pass as array: `$stmt->execute([$param1, $param2])`
- C++: Use `prepare()` with proper parameter count

### Invalid JSON
**Symptom**: `invalid input syntax for type json`

**Causes**:
- Returning invalid JSON format
- Not aggregating properly with json_agg
- NULL values not handled

**Solutions**:
- Use `COALESCE(json_agg(...), '[]'::json)` for empty results
- Wrap json_agg in a subquery if needed
- Test JSON output: `SELECT jsonb_pretty(your_json_column)`

## Docker Networking Issues

### Service Not Found
**Symptom**: `could not resolve hostname` or `unknown host`

**Causes**:
- Services not on same Docker network
- Using wrong service name

**Solutions**:
- Check docker-compose.yml network configuration
- Use service names from docker-compose.yml (e.g., `postgres`, `redis`)
- Verify with: `docker network inspect <network-name>`

### Port Already in Use
**Symptom**: `port is already allocated`

**Causes**:
- Another container using the same port
- Port conflict on host machine

**Solutions**:
```bash
# Find what's using the port
lsof -i :5432
netstat -tulpn | grep 5432

# Stop conflicting container or change port in docker-compose.yml
```

## Performance Issues

### Slow Queries
**Symptom**: Queries taking > 1 second

**Causes**:
- Missing indexes
- Large JOINs without proper conditions
- N+1 query problems

**Solutions**:
- Check query execution plan: `EXPLAIN ANALYZE <your-query>`
- Ensure foreign key columns are indexed
- Use JOINs instead of multiple queries
- Consider query complexity vs requirements

### Cache Not Helping
**Symptom**: Same response time with and without cache

**Causes**:
- Cache not being checked
- Keys not matching between set and get
- TTL too short

**Solutions**:
- Add logging to verify cache hits/misses
- Debug key generation consistency
- Check Redis memory: `redis-cli -h redis INFO memory`

## Debugging Tips

### Enable SQL Logging
Add to your database connection setup to see executed queries:

**Python (psycopg2)**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**PHP (PDO)**:
```php
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
```

### Print/Log Variables
When debugging, output key information:
- Connection strings (without passwords!)
- Query parameters
- Cache keys
- Response data

### Use Docker Logs
```bash
# Follow logs in real-time
docker logs -f <container-name>

# View last N lines
docker logs --tail 100 <container-name>
```

### Test Components Separately
1. Test database connection first
2. Then test simple queries
3. Add Redis caching last
4. Test each endpoint individually

## Common Mistakes

1. **Not handling NULL values** - Use COALESCE in SQL
2. **Closing connections too early** - Keep connection alive for query execution
3. **Not using parameterized queries** - Always use placeholders for security
4. **Hardcoding configuration** - Always use environment variables
5. **Not checking return values** - Verify connections succeed before using
6. **Cache key collisions** - Use unique, descriptive keys
7. **Forgetting JSON format** - Endpoints should return valid JSON
8. **Not setting Content-Type** - Always set `Content-Type: application/json`

## Getting Help

If you're still stuck after checking this guide:

1. Check your code against the specification in LAB05.md
2. Review the query examples in LAB05-QUERIES.md
3. Verify your environment setup
4. Test with curl or Postman to isolate issues
5. Check both imgprocessor and database container logs

Remember: Most issues are configuration or connection-related, not code logic!
