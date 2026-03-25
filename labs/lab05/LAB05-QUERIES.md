# LAB05: SQL Query Requirements

This document describes the SQL queries and caching logic you need to implement for the Users and Images endpoints.

**Note:** The Operations and Jobs endpoints are provided as complete working examples. Study their implementations to understand the full pattern including caching.

## Caching Requirement

**Both endpoints must implement Redis caching.** This is a core learning objective of the lab.

### Caching Pattern

For each endpoint, you must:

1. **Check cache first** using the appropriate cache key:
   - Users: `'admin:users'`
   - Images: `'admin:images'`

2. **If cache hit:**
   - Parse cached JSON data
   - Set `cached` flag to `true`
   - Return the response immediately

3. **If cache miss:**
   - Execute SQL query (see below)
   - Format response as JSON with:
     - Data array (users or images)
     - `cached: false`
     - `cache_ttl: 300` (5 minutes)
   - Store JSON in cache with TTL of 300 seconds
   - Return the response

Study the provided Operations and Jobs endpoints to see this pattern implemented correctly.

## Database Schema

The admin interface expects these tables:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Images table
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    original_filename VARCHAR(255) NOT NULL,
    minio_key VARCHAR(255) NOT NULL,
    file_size INTEGER,
    content_type VARCHAR(50),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table
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

## Your Tasks

You need to write SQL queries for two endpoints:

### 1. Users Endpoint (`/api/users`)

**Objective:** Return a list of all users with their image and job counts.

**Required Fields:**
- `id` - User ID
- `username` - Username
- `created_at` - Account creation timestamp
- `image_count` - Count of images uploaded by user
- `job_count` - Count of jobs created by user

**Requirements:**
- Include users even if they have no images or jobs (use LEFT JOIN)
- Use COUNT(DISTINCT ...) to avoid double-counting when joining multiple tables
- Group by user to aggregate counts
- Order by creation date (newest first)

**Hints:**
- Use `COUNT(DISTINCT i.id)` and `COUNT(DISTINCT j.id)` to count related records
- Use `LEFT JOIN` to include users with zero images/jobs
- Group by all non-aggregated fields (u.id, u.username, u.created_at)

### 2. Images Endpoint (`/api/images`)

**Objective:** Return recent images with user information.

**Required Fields:**
- `id` - Image ID
- `user_id` - Owner user ID
- `username` - Owner username
- `original_filename` - Original file name
- `file_size` - File size in bytes
- `content_type` - MIME type
- `upload_date` - Upload timestamp

**Requirements:**
- Join with users table to get username
- Order by upload date (newest first)
- Limit to 100 most recent images

**Hints:**
- Use `INNER JOIN` since every image must have a user
- Order by timestamp descending for newest first
- Use `LIMIT` clause

## Example Query Pattern

Study the provided Operations and Jobs endpoints in your language's `endpoints.*` file to see:
- How to structure multi-table queries
- How to use aggregation functions
- How to format results for JSON responses

General pattern:
```sql
-- Pattern for aggregation with LEFT JOIN
SELECT 
    t1.field1,
    t1.field2,
    COUNT(DISTINCT t2.id) as count_field
FROM table1 t1
LEFT JOIN table2 t2 ON t1.id = t2.foreign_key
GROUP BY t1.field1, t1.field2
ORDER BY t1.field1 DESC;

-- Pattern for INNER JOIN with filtering
SELECT 
    t1.field1,
    t2.field2,
    t1.field3
FROM table1 t1
INNER JOIN table2 t2 ON t1.id = t2.foreign_key
ORDER BY t1.timestamp DESC
LIMIT 100;
```

## Security Requirements

- **Always use parameterized queries** to prevent SQL injection
- Do NOT concatenate user input into SQL strings
- Use your language's parameterized query mechanism:
  - Python: `cursor.execute(query, (param1, param2))`
  - PHP: `$stmt->execute([$param1, $param2])`
  - C++: `txn.exec_params(query, param1, param2)`

## Testing Your Queries

Test your queries directly in PostgreSQL first:

```bash
# Connect to database
psql -h host -U user -d database

# Test users query
SELECT ... FROM users ... ;

# Test images query
SELECT ... FROM images ... ;
```

Verify:
- All required fields are present
- Counts are correct
- Results are ordered properly
- Query executes without errors

## Common Issues

- **Missing users with zero images/jobs**: Use LEFT JOIN, not INNER JOIN
- **Duplicate rows**: Use COUNT(DISTINCT ...) instead of COUNT(...)
- **Incorrect ordering**: Check your ORDER BY clause
- **SQL injection risk**: Always use parameterized queries
