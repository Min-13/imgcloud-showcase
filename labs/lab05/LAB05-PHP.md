# Lab 05 - PHP Implementation Guide

This guide provides PHP-specific implementation details for Lab 05. Refer to [LAB05.md](LAB05.md) for requirements and [LAB05-QUERIES.md](LAB05-QUERIES.md) for query examples.

## File Structure

Create these files in your `imgprocessor/` directory:

```
imgprocessor/
├── db.php          # Database connection management
├── cache.php       # Redis cache implementation
└── endpoints.php   # Query endpoint implementations (or separate files per query)
```

## Required Extensions

Ensure these are enabled in your PHP installation:

```ini
extension=pdo_pgsql
extension=redis
```

For Dockerfile:
```dockerfile
RUN docker-php-ext-install pdo pgsql pdo_pgsql
RUN pecl install redis && docker-php-ext-enable redis
```

## Database Connection (`db.php`)

### URL Parsing

Use `parse_url()` to parse DATABASE_URL:

```php
<?php

function parseDatabaseUrl($url) {
    $parsed = parse_url($url);
    
    return [
        'host' => $parsed['host'],
        'port' => $parsed['port'] ?? 5432,
        'database' => ltrim($parsed['path'], '/'),
        'username' => $parsed['user'],
        'password' => $parsed['pass']
    ];
}

$db_url = getenv('DATABASE_URL');
$config = parseDatabaseUrl($db_url);
```

### PDO Connection with Persistent Connections

```php
<?php

class Database {
    private static $instance = null;
    private $pdo;
    
    private function __construct() {
        $db_url = getenv('DATABASE_URL');
        $config = $this->parseDatabaseUrl($db_url);
        
        $dsn = sprintf(
            "pgsql:host=%s;port=%d;dbname=%s",
            $config['host'],
            $config['port'],
            $config['database']
        );
        
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_PERSISTENT => true,  // Persistent connections
            PDO::ATTR_EMULATE_PREPARES => false
        ];
        
        $this->pdo = new PDO(
            $dsn,
            $config['username'],
            $config['password'],
            $options
        );
    }
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    public function getConnection() {
        return $this->pdo;
    }
    
    private function parseDatabaseUrl($url) {
        // Implementation from above
    }
}
```

### Global Instance Variables

**IMPORTANT**: At the end of `db.php` and `cache.php`, you must create global instances that the endpoint files can access:

```php
// At the end of db.php
$db = Database::getInstance();
```

```php
// At the end of cache.php
$cache = CacheManager::getInstance();
```

These global variables (`$db` and `$cache`) are used by `endpoints.php` to access the database and cache. Without them, you'll get "undefined variable" errors.

### Using the Connection

```php
<?php

// Access the global $db instance
global $db;
$pdo = $db->getConnection();

// Execute query
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([1]);
$user = $stmt->fetch();
```

## Redis Cache (`cache.php`)

### Connection Setup

```php
<?php

class CacheManager {
    private static $instance = null;
    private $redis;
    
    private function __construct() {
        $redis_url = getenv('REDIS_URL') ?: 'redis://redis:6379';
        $parsed = parse_url($redis_url);
        
        $this->redis = new Redis();
        $this->redis->connect(
            $parsed['host'],
            $parsed['port'] ?? 6379
        );
        
        // Optional: authentication if needed
        if (isset($parsed['pass'])) {
            $this->redis->auth($parsed['pass']);
        }
    }
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    public function get($key) {
        $value = $this->redis->get($key);
        return $value !== false ? $value : null;
    }
    
    public function set($key, $value, $ttl = 300) {
        return $this->redis->setex($key, $ttl, $value);
    }
    
    public function delete($key) {
        return $this->redis->del($key);
    }
}
```

### Cache Key Generation

```php
<?php

function generateCacheKey($queryName, $params) {
    // Sort params for consistency
    ksort($params);
    $paramStr = json_encode($params);
    $paramHash = md5($paramStr);
    return "query:{$queryName}:{$paramHash}";
}
```

## Parameterized Queries for SQL Injection Prevention

### Why Parameterized Queries?

**Never** build SQL queries with string concatenation:

```php
<?php

// ❌ DANGEROUS - SQL Injection Vulnerable
$user_id = $_GET['user_id'];
$query = "SELECT * FROM users WHERE id = $user_id";  // NEVER DO THIS!
$stmt = $pdo->query($query);

// ❌ ALSO DANGEROUS
$query = "SELECT * FROM users WHERE id = " . $user_id;  // NEVER DO THIS!
$stmt = $pdo->query($query);

// ❌ STILL DANGEROUS
$query = sprintf("SELECT * FROM users WHERE id = %s", $user_id);  // NEVER DO THIS!
$stmt = $pdo->query($query);
```

**Why it's dangerous:** Attacker can inject SQL:
```php
$user_id = "1 OR 1=1; DROP TABLE users; --";
// Results in: SELECT * FROM users WHERE id = 1 OR 1=1; DROP TABLE users; --
```

### Using Placeholders Safely

PHP PDO supports two types of placeholders:

#### Positional Placeholders (?)

```php
<?php

// ✅ SAFE - Single parameter
$user_id = filter_input(INPUT_GET, 'user_id', FILTER_VALIDATE_INT);
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$user_id]);

// ✅ SAFE - Multiple parameters
$stmt = $pdo->prepare("SELECT * FROM images WHERE user_id = ? AND created_at > ?");
$stmt->execute([$user_id, $date_threshold]);

// ✅ SAFE - String parameters (automatically escaped)
$username = $_GET['username'] ?? '';
$stmt = $pdo->prepare("SELECT * FROM users WHERE username = ?");
$stmt->execute([$username]);  // PDO automatically escapes quotes

// ✅ SAFE - IN clause with multiple values
$ids = [1, 2, 3, 4];
$placeholders = str_repeat('?,', count($ids) - 1) . '?';
$stmt = $pdo->prepare("SELECT * FROM images WHERE id IN ($placeholders)");
$stmt->execute($ids);
```

#### Named Placeholders (:name)

```php
<?php

// ✅ SAFE - Named placeholders (more readable)
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id AND active = :active");
$stmt->execute(['id' => 123, 'active' => true]);

// ✅ SAFE - Can reuse same name
$stmt = $pdo->prepare("
    SELECT * FROM images 
    WHERE width >= :size AND height >= :size
");
$stmt->execute(['size' => 800]);

// ✅ SAFE - Mixed with complex queries
$stmt = $pdo->prepare("
    SELECT * FROM users 
    WHERE username = :username 
    AND created_at BETWEEN :start_date AND :end_date
");
$stmt->execute([
    'username' => $username,
    'start_date' => $start_date,
    'end_date' => $end_date
]);
```

### How Parameterized Queries Work

PDO sends the query and parameters **separately** to PostgreSQL:

1. Query template sent: `SELECT * FROM users WHERE id = $1`
2. Parameters sent separately: `[123]`
3. PostgreSQL treats parameters as **data**, never as SQL code
4. Result: SQL injection is **impossible**

### Additional Safety Tips

```php
<?php

// Always validate input types
$user_id = filter_input(INPUT_GET, 'user_id', FILTER_VALIDATE_INT);
if ($user_id === false || $user_id === null) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid user_id']);
    exit;
}

// Use explicit type binding for integers
$stmt = $pdo->prepare("SELECT * FROM images LIMIT ?");
$limit = 50;
$stmt->bindValue(1, $limit, PDO::PARAM_INT);
$stmt->execute();

// For dynamic column names (can't be parameterized), use whitelisting
$allowed_columns = ['id', 'username', 'email', 'created_at'];
$sort_by = $_GET['sort_by'] ?? 'id';
if (!in_array($sort_by, $allowed_columns)) {
    $sort_by = 'id';
}
// Now safe to use in query
$stmt = $pdo->query("SELECT * FROM users ORDER BY {$sort_by}");  // OK because whitelisted

// NEVER trust user input for table names or column names without whitelisting
```

### PDO Configuration for Security

```php
<?php

$options = [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES => false,  // ✅ IMPORTANT: Use real prepared statements
    PDO::ATTR_PERSISTENT => true
];

$pdo = new PDO($dsn, $username, $password, $options);
```

**Key setting:** `PDO::ATTR_EMULATE_PREPARES => false` ensures PDO uses **real** prepared statements (server-side), not emulated ones (client-side string replacement).

### Fetching Results

```php
<?php

// Fetch all rows as associative array
$stmt = $pdo->prepare("SELECT id, username FROM users");
$stmt->execute();
$users = $stmt->fetchAll(PDO::FETCH_ASSOC);
// Result: [['id' => 1, 'username' => 'alice'], ['id' => 2, 'username' => 'bob']]

// Fetch one row
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([123]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);
// Result: ['id' => 123, 'username' => 'alice'] or false

// Fetch single column
$stmt = $pdo->prepare("SELECT username FROM users");
$stmt->execute();
$usernames = $stmt->fetchAll(PDO::FETCH_COLUMN);
// Result: ['alice', 'bob', 'charlie']
```

## Query Endpoint Pattern

### Basic Structure

```php
<?php

require_once 'db.php';
require_once 'cache.php';

header('Content-Type: application/json');

// Get request parameters
$user_id = $_GET['user_id'] ?? null;

if ($user_id === null) {
    http_response_code(400);
    echo json_encode(['error' => 'user_id required']);
    exit;
}

// Get instances
$cache = CacheManager::getInstance();
$db = Database::getInstance();
$pdo = $db->getConnection();

// Generate cache key
$cache_key = generateCacheKey('query1', ['user_id' => $user_id]);

// Check cache
$cached = $cache->get($cache_key);
if ($cached !== null) {
    echo $cached;
    exit;
}

// Execute query
try {
    $stmt = $pdo->prepare("
        SELECT column1, column2
        FROM table_name
        WHERE user_id = ?
    ");
    $stmt->execute([$user_id]);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Format response
    $result = [
        'data' => $rows
    ];
    
    // Cache result
    $json_result = json_encode($result);
    $cache->set($cache_key, $json_result, 300);
    
    // Return response
    echo $json_result;
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
}
```

### Handling JSON Aggregation

When SQL returns JSON (from json_agg):

```php
<?php

$stmt = $pdo->prepare("
    SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
    FROM (
        SELECT id, username, email
        FROM users
        WHERE created_at > ?
    ) t
");
$stmt->execute([$date_threshold]);
$json_result = $stmt->fetchColumn();

// $json_result is already a JSON string from PostgreSQL
$result = ['users' => json_decode($json_result)];
echo json_encode($result);
```

### Error Handling

```php
<?php

try {
    // Query logic
    $stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();
    
    if (!$user) {
        http_response_code(404);
        echo json_encode(['error' => 'User not found']);
        exit;
    }
    
    echo json_encode(['user' => $user]);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Database error',
        'message' => $e->getMessage()
    ]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Unexpected error',
        'message' => $e->getMessage()
    ]);
}
```

## Complete Endpoint Example Pattern

```php
<?php

require_once 'db.php';
require_once 'cache.php';

header('Content-Type: application/json');

/**
 * Get all images for a user with metadata
 */
function getUserImages() {
    // Validate input
    $user_id = filter_input(INPUT_GET, 'user_id', FILTER_VALIDATE_INT);
    if ($user_id === false || $user_id === null) {
        http_response_code(400);
        return ['error' => 'user_id required'];
    }
    
    // Check cache
    $cache = CacheManager::getInstance();
    $cache_key = "query:user_images:{$user_id}";
    $cached = $cache->get($cache_key);
    
    if ($cached !== null) {
        return json_decode($cached, true);
    }
    
    // Query database
    try {
        $db = Database::getInstance();
        $pdo = $db->getConnection();
        
        $stmt = $pdo->prepare("
            SELECT 
                i.id,
                i.filename,
                i.size,
                i.created_at,
                COUNT(t.id) as tag_count
            FROM images i
            LEFT JOIN image_tags it ON i.id = it.image_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE i.user_id = ?
            GROUP BY i.id
            ORDER BY i.created_at DESC
        ");
        
        $stmt->execute([$user_id]);
        $images = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Format dates
        foreach ($images as &$image) {
            if ($image['created_at']) {
                $image['created_at'] = date('c', strtotime($image['created_at']));
            }
            $image['tag_count'] = (int)$image['tag_count'];
        }
        
        $result = ['images' => $images];
        
        // Cache result
        $cache->set($cache_key, json_encode($result), 300);
        
        return $result;
        
    } catch (PDOException $e) {
        http_response_code(500);
        return ['error' => 'Database error: ' . $e->getMessage()];
    }
}

echo json_encode(getUserImages());
```

## Testing Tips

### Test Database Connection

```php
<?php

function testConnection() {
    try {
        $db = Database::getInstance();
        $pdo = $db->getConnection();
        
        $stmt = $pdo->query("SELECT version()");
        $version = $stmt->fetchColumn();
        
        echo "Connected to: $version\n";
        return true;
    } catch (Exception $e) {
        echo "Connection failed: " . $e->getMessage() . "\n";
        return false;
    }
}

testConnection();
```

### Test Redis Connection

```php
<?php

function testRedis() {
    try {
        $cache = CacheManager::getInstance();
        
        $cache->set('test_key', 'test_value', 10);
        $value = $cache->get('test_key');
        
        if ($value === 'test_value') {
            echo "Redis connection OK\n";
            $cache->delete('test_key');
            return true;
        } else {
            echo "Redis test failed\n";
            return false;
        }
    } catch (Exception $e) {
        echo "Redis failed: " . $e->getMessage() . "\n";
        return false;
    }
}

testRedis();
```

## Common Patterns

### Optional Parameters

```php
<?php

function searchImages() {
    $user_id = filter_input(INPUT_GET, 'user_id', FILTER_VALIDATE_INT);
    $tag = $_GET['tag'] ?? null;
    $limit = filter_input(INPUT_GET, 'limit', FILTER_VALIDATE_INT) ?: 50;
    
    $query = "SELECT * FROM images WHERE 1=1";
    $params = [];
    
    if ($user_id !== null && $user_id !== false) {
        $query .= " AND user_id = ?";
        $params[] = $user_id;
    }
    
    if ($tag !== null) {
        $query .= " AND EXISTS (
            SELECT 1 FROM image_tags it 
            JOIN tags t ON it.tag_id = t.id 
            WHERE it.image_id = images.id AND t.name = ?
        )";
        $params[] = $tag;
    }
    
    $query .= " LIMIT ?";
    $params[] = $limit;
    
    $pdo = Database::getInstance()->getConnection();
    $stmt = $pdo->prepare($query);
    $stmt->execute($params);
    
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}
```

### Pagination

```php
<?php

$page = filter_input(INPUT_GET, 'page', FILTER_VALIDATE_INT) ?: 1;
$per_page = filter_input(INPUT_GET, 'per_page', FILTER_VALIDATE_INT) ?: 20;

$offset = ($page - 1) * $per_page;

$stmt = $pdo->prepare("
    SELECT * FROM images
    ORDER BY created_at DESC
    LIMIT ? OFFSET ?
");

// Note: Use bindValue with PDO::PARAM_INT for integer parameters when you need
// explicit type binding. For most cases, execute([$per_page, $offset]) works fine.
$stmt->bindValue(1, $per_page, PDO::PARAM_INT);
$stmt->bindValue(2, $offset, PDO::PARAM_INT);
$stmt->execute();

$images = $stmt->fetchAll(PDO::FETCH_ASSOC);
```

### Input Validation

```php
<?php

// Validate integer
$id = filter_input(INPUT_GET, 'id', FILTER_VALIDATE_INT);
if ($id === false || $id === null) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid id']);
    exit;
}

// Validate email
$email = filter_input(INPUT_GET, 'email', FILTER_VALIDATE_EMAIL);
if ($email === false) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email']);
    exit;
}

// Validate string with regex
$username = $_GET['username'] ?? '';
if (!preg_match('/^[a-zA-Z0-9_]{3,20}$/', $username)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid username']);
    exit;
}
```

## Router Pattern (Optional)

For multiple endpoints in one file:

```php
<?php

require_once 'db.php';
require_once 'cache.php';

header('Content-Type: application/json');

$request_uri = $_SERVER['REQUEST_URI'];
$path = parse_url($request_uri, PHP_URL_PATH);

try {
    switch ($path) {
        case '/api/query1':
            echo json_encode(handleQuery1());
            break;
        case '/api/query2':
            echo json_encode(handleQuery2());
            break;
        case '/api/query3':
            echo json_encode(handleQuery3());
            break;
        default:
            http_response_code(404);
            echo json_encode(['error' => 'Endpoint not found']);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}

function handleQuery1() {
    // Implementation
}

function handleQuery2() {
    // Implementation
}
```

## References

- [PHP PDO documentation](https://www.php.net/manual/en/book.pdo.php)
- [phpredis documentation](https://github.com/phpredis/phpredis)
- [PostgreSQL PHP documentation](https://www.php.net/manual/en/ref.pgsql.php)
- [LAB05.md](LAB05.md) - Main lab requirements
- [LAB05-QUERIES.md](LAB05-QUERIES.md) - Query examples
- [LAB05-REDIS.md](LAB05-REDIS.md) - Redis caching guide and testing
- [LAB05-TROUBLESHOOTING.md](LAB05-TROUBLESHOOTING.md) - Common issues
