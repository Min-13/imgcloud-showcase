# LAB05: Regular Expressions Guide

This guide explains how to use regular expressions for URL parsing and validation in Lab05.

## Table of Contents

1. [Why Regular Expressions?](#why-regular-expressions)
2. [URL Parsing Patterns](#url-parsing-patterns)
3. [Python Regular Expressions](#python-regular-expressions)
4. [PHP Regular Expressions](#php-regular-expressions)
5. [C++ Regular Expressions](#c-regular-expressions)
6. [Best Practices](#best-practices)
7. [Testing Your Patterns](#testing-your-patterns)

## Why Regular Expressions?

Regular expressions (regex) are patterns used to match character combinations in strings. In Lab05, you'll use them to:

1. **Parse DATABASE_URL and REDIS_URL** - Extract host, port, database name from connection strings
2. **Validate input** - Ensure data matches expected formats
3. **Extract components** - Pull specific parts from structured strings

### Connection String Formats

**DATABASE_URL:**
```
postgresql://user:password@hostname:port/database
```

**REDIS_URL:**
```
redis://hostname:port/db_number
```

## URL Parsing Patterns

### Understanding URL Structure

Before parsing, understand the structure you're working with:

**DATABASE_URL format:**
```
scheme://username:password@hostname:port/database_name
```

**REDIS_URL format:**
```
scheme://hostname:port/database_number
```

### Pattern Components

When building a regex pattern, consider these components:

- **Scheme**: `postgresql://` or `redis://` (literal match)
- **Username/Password**: Characters before `@` (for database URLs)
- **Hostname**: Characters between `@` and `:` or between `://` and `:`
- **Port**: Numeric digits after `:`
- **Path/Database**: Characters after final `/`

### Example: Parsing a Simple URL

Here's an example of parsing a generic URL format:

```
protocol://host:port/path
```

**Example regex pattern for educational purposes:**
```regex
^(\w+)://([^:]+):(\d+)/(.+)$
```

This pattern captures:
1. Protocol (word characters)
2. Hostname (anything except colon)
3. Port (digits)
4. Path (remaining characters)

**Note:** This is a simplified example. Your actual DATABASE_URL and REDIS_URL will have additional complexity (like authentication credentials) that you'll need to handle.

### Alternative Approaches

Instead of building complex regex patterns from scratch, consider:

**Option 1: Regex for validation, string split for extraction**
- Use regex to validate the URL format is correct
- Then use string operations (split, substring) to extract individual components
- This approach is often simpler and more maintainable

**Option 2: URL parsing libraries** (recommended)
- Python: `urllib.parse.urlparse()`
- PHP: `parse_url()`
- C++: Manual string parsing or third-party library

## Python Regular Expressions

### Import and Basic Usage

```python
import re

# Example: Parsing a generic URL with authentication
pattern = r"^(\w+)://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)$"
example_url = "myprotocol://user123:pass456@example.com:5000/database"

match = re.match(pattern, example_url)
if match:
    protocol = match.group(1)   # "myprotocol"
    username = match.group(2)   # "user123"
    password = match.group(3)   # "pass456"
    hostname = match.group(4)   # "example.com"
    port = int(match.group(5))  # 5000
    dbname = match.group(6)     # "database"
```

**Your task:** Adapt this pattern for the specific DATABASE_URL format you're working with.

### Named Groups (Recommended)

Named groups make your code more readable:

```python
pattern = r"^(?P<proto>\w+)://(?P<user>[^:]+):(?P<pass>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<db>.+)$"

match = re.match(pattern, url)
if match:
    user = match.group('user')
    password = match.group('pass')
    host = match.group('host')
    port = int(match.group('port'))
    database = match.group('db')
```

### Recommended Approach: Use urlparse

Python's built-in `urlparse` is often easier than regex:

```python
from urllib.parse import urlparse

# Example with generic database URL
example_url = "dbprotocol://user:pass@host:5432/dbname"
parsed = urlparse(example_url)

# Access components:
# parsed.scheme = "dbprotocol"
# parsed.hostname = "host"
# parsed.port = 5432
# parsed.username = "user"
# parsed.password = "pass"
# parsed.path = "/dbname" (remember to remove leading /)
```

### Error Handling

Always validate and handle parsing errors:

```python
def parse_connection_url(url):
    """Parse a database connection URL with error handling."""
    pattern = r"^(\w+)://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)$"
    match = re.match(pattern, url)
    
    if not match:
        raise ValueError(f"Invalid URL format: {url}")
    
    return {
        'protocol': match.group(1),
        'user': match.group(2),
        'password': match.group(3),
        'host': match.group(4),
        'port': int(match.group(5)),
        'database': match.group(6)
    }
```

## PHP Regular Expressions

### Basic Pattern Matching

PHP uses PCRE (Perl-Compatible Regular Expressions):

```php
// Example: Parsing a URL with authentication
$example_url = "protocol://username:password@hostname:5000/database";
$pattern = "/^(\w+):\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)$/";

if (preg_match($pattern, $example_url, $matches)) {
    $protocol = $matches[1];  // "protocol"
    $user = $matches[2];      // "username"
    $password = $matches[3];  // "password"
    $host = $matches[4];      // "hostname"
    $port = (int)$matches[5]; // 5000
    $database = $matches[6];  // "database"
}
```

**Your task:** Modify this pattern to match your actual DATABASE_URL and REDIS_URL formats.

### Named Capture Groups

Named groups make patterns more readable:

```php
// Example pattern with named groups
$pattern = "/^(?P<proto>\w+):\/\/(?P<user>[^:]+):(?P<pass>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)\/(?P<db>.+)$/";

if (preg_match($pattern, $example_url, $matches)) {
    $protocol = $matches['proto'];
    $user = $matches['user'];
    $password = $matches['pass'];
    $host = $matches['host'];
    $port = (int)$matches['port'];
    $database = $matches['db'];
}
```

### Recommended Approach: Use parse_url

PHP's built-in `parse_url` is easier than regex:

```php
// Example with generic URL
$example_url = "protocol://user:pass@host:5000/database";
$parsed = parse_url($example_url);

// Access components:
// $parsed['scheme'] = "protocol"
// $parsed['host'] = "host"
// $parsed['port'] = 5000
// $parsed['user'] = "user"
// $parsed['pass'] = "pass"
// $parsed['path'] = "/database" (remove leading /)
```

### Error Handling

```php
function parseConnectionUrl($url) {
    $pattern = "/^(\w+):\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)$/";
    
    if (!preg_match($pattern, $url, $matches)) {
        throw new Exception("Invalid URL format: " . $url);
    }
    
    return [
        'protocol' => $matches[1],
        'user' => $matches[2],
        'password' => $matches[3],
        'host' => $matches[4],
        'port' => (int)$matches[5],
        'database' => $matches[6]
    ];
}
```

## C++ Regular Expressions

### Include Required Headers

```cpp
#include <regex>
#include <string>
```

### Basic Pattern Matching

```cpp
// Example: Parsing a URL with authentication
std::string example_url = "protocol://user:pass@host:5000/database";
std::regex pattern("^(\\w+)://([^:]+):([^@]+)@([^:]+):(\\d+)/(.+)$");
std::smatch matches;

if (std::regex_match(example_url, matches, pattern)) {
    std::string protocol = matches[1].str();  // "protocol"
    std::string user = matches[2].str();      // "user"
    std::string password = matches[3].str();  // "pass"
    std::string host = matches[4].str();      // "host"
    int port = std::stoi(matches[5].str());   // 5000
    std::string database = matches[6].str();  // "database"
}
```

**Your task:** Adapt this pattern for your specific DATABASE_URL and REDIS_URL formats.

### Recommended Approach: Manual String Parsing

Since C++ doesn't have built-in URL parsing like Python/PHP, manual parsing is often simpler and more maintainable:

```cpp
struct ConnectionConfig {
    std::string protocol;
    std::string user;
    std::string password;
    std::string host;
    int port;
    std::string database;
};

ConnectionConfig parseConnectionUrl(const std::string& url) {
    // Example: Parse "protocol://user:pass@host:port/database"
    
    // 1. Extract protocol
    size_t pos = url.find("://");
    if (pos == std::string::npos) {
        throw std::runtime_error("Invalid URL format");
    }
    std::string protocol = url.substr(0, pos);
    std::string rest = url.substr(pos + 3);
    
    // 2. Extract credentials (before @)
    pos = rest.find('@');
    std::string credentials = rest.substr(0, pos);
    rest = rest.substr(pos + 1);
    
    size_t colon = credentials.find(':');
    std::string user = credentials.substr(0, colon);
    std::string password = credentials.substr(colon + 1);
    
    // 3. Extract host and port (before /)
    pos = rest.find('/');
    std::string hostport = rest.substr(0, pos);
    std::string database = rest.substr(pos + 1);
    
    colon = hostport.find(':');
    std::string host = hostport.substr(0, colon);
    int port = std::stoi(hostport.substr(colon + 1));
    
    return {protocol, user, password, host, port, database};
}
```

### Error Handling

Always validate input and handle errors:

```cpp
ConnectionConfig parseConnectionUrl(const std::string& url) {
    std::regex pattern("^(\\w+)://([^:]+):([^@]+)@([^:]+):(\\d+)/(.+)$");
    std::smatch matches;
    
    if (!std::regex_match(url, matches, pattern)) {
        throw std::runtime_error("Invalid URL format: " + url);
    }
    
    return {
        matches[1].str(),           // user
        matches[2].str(),           // password
        matches[3].str(),           // host
        std::stoi(matches[4].str()), // port
        matches[5].str()            // database
    };
}
```

## Best Practices

### 1. Use Built-in URL Parsers When Available

**Python and PHP** have excellent URL parsing libraries:
- Python: `urllib.parse.urlparse()`
- PHP: `parse_url()`

These are more reliable than regex for general URL parsing.

### 2. Escape Special Characters

In regex patterns, escape these special characters: `. * + ? ^ $ ( ) [ ] { } | \`

```python
# Wrong: Treats . as "any character"
pattern = r"http://example.com"

# Right: Escapes . to match literal dot
pattern = r"http://example\.com"
```

### 3. Use Raw Strings

**Python:** Use `r"pattern"` to avoid double-escaping backslashes

```python
# Wrong: Need double backslashes
pattern = "\\d+"

# Right: Raw string with single backslash
pattern = r"\d+"
```

**C++:** Escape backslashes in normal strings

```cpp
// Need double backslashes in C++
std::regex pattern("\\d+");
```

### 4. Validate Before Parsing

Always validate the format before trying to extract components:

```python
if not re.match(r"^postgresql://", url):
    raise ValueError("Not a PostgreSQL URL")
```

### 5. Handle Optional Components

Use `(?:...)?` for optional groups:

```regex
redis://host:port(?:/db)?
```

The `(?:...)` is a non-capturing group, and `?` makes it optional.

### 6. Test Edge Cases

Test your regex with:
- Minimum valid input
- Maximum valid input
- Invalid formats
- Missing optional components
- Special characters in passwords

## Testing Your Patterns

### Python Testing

```python
import re

def test_pattern():
    pattern = r"^postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)$"
    
    # Valid cases
    assert re.match(pattern, "postgresql://user:pass@host:5432/db")
    assert re.match(pattern, "postgresql://admin:secret123@db-1:5432/myapp")
    
    # Invalid cases
    assert not re.match(pattern, "mysql://user:pass@host:5432/db")
    assert not re.match(pattern, "postgresql://user@host:5432/db")  # Missing password
    assert not re.match(pattern, "postgresql://user:pass@host/db")  # Missing port
    
    print("All tests passed!")

test_pattern()
```

### PHP Testing

```php
function testPattern() {
    $pattern = "/^postgresql:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)$/";
    
    // Valid cases
    assert(preg_match($pattern, "postgresql://user:pass@host:5432/db"));
    assert(preg_match($pattern, "postgresql://admin:secret123@db-1:5432/myapp"));
    
    // Invalid cases
    assert(!preg_match($pattern, "mysql://user:pass@host:5432/db"));
    assert(!preg_match($pattern, "postgresql://user@host:5432/db"));
    assert(!preg_match($pattern, "postgresql://user:pass@host/db"));
    
    echo "All tests passed!\n";
}

testPattern();
```

### C++ Testing

```cpp
#include <regex>
#include <cassert>
#include <iostream>

void testPattern() {
    std::regex pattern("^postgresql://([^:]+):([^@]+)@([^:]+):(\\d+)/(.+)$");
    
    // Valid cases
    assert(std::regex_match("postgresql://user:pass@host:5432/db", pattern));
    assert(std::regex_match("postgresql://admin:secret123@db-1:5432/myapp", pattern));
    
    // Invalid cases
    assert(!std::regex_match("mysql://user:pass@host:5432/db", pattern));
    assert(!std::regex_match("postgresql://user@host:5432/db", pattern));
    assert(!std::regex_match("postgresql://user:pass@host/db", pattern));
    
    std::cout << "All tests passed!" << std::endl;
}

int main() {
    testPattern();
    return 0;
}
```

### Online Regex Testers

Practice your patterns with online tools:
- **regex101.com** - Excellent explanations and debugging
- **regexr.com** - Visual pattern breakdown
- **regexpal.com** - Simple testing interface

## Common Patterns Reference

### Character Classes

- `\d` - Any digit (0-9)
- `\w` - Any word character (a-z, A-Z, 0-9, _)
- `\s` - Any whitespace character
- `.` - Any character (except newline)
- `[abc]` - Any of a, b, or c
- `[^abc]` - Any character except a, b, or c
- `[a-z]` - Any lowercase letter
- `[0-9]` - Any digit

### Quantifiers

- `*` - 0 or more times
- `+` - 1 or more times
- `?` - 0 or 1 time (optional)
- `{n}` - Exactly n times
- `{n,}` - n or more times
- `{n,m}` - Between n and m times

### Anchors

- `^` - Start of string
- `$` - End of string
- `\b` - Word boundary

### Groups

- `(...)` - Capturing group
- `(?:...)` - Non-capturing group
- `(?P<name>...)` - Named group (Python)
- `(?<name>...)` - Named group (PHP, C++)

## Lab05-Specific Recommendations

For this lab, we recommend:

1. **Use built-in URL parsers** (`urlparse()` in Python, `parse_url()` in PHP) for parsing DATABASE_URL and REDIS_URL
2. **Use regex for validation** to ensure the URL format is correct before parsing
3. **Use regex for extraction** only if you're comfortable with it, otherwise stick to string operations
4. **Test thoroughly** with the examples in this guide

### Example: Combined Approach

```python
from urllib.parse import urlparse
import re

def parse_and_validate_db_url(url):
    # First, validate format with regex
    if not re.match(r"^postgresql://[^:]+:[^@]+@[^:]+:\d+/.+$", url):
        raise ValueError(f"Invalid DATABASE_URL format: {url}")
    
    # Then use urlparse for extraction
    parsed = urlparse(url)
    
    return {
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path.lstrip('/')
    }
```

This combines the strengths of both approaches: regex for validation, URL parser for extraction.
