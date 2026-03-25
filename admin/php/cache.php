<?php
/**
 * Redis cache module for LAB05
 * Provides simple caching interface with TTL support
 */

class CacheManager {
    private static $instance = null;
    private $redis;
    
    /**
     * Private constructor - singleton pattern
     */
    private function __construct() {
        $redis_url = getenv('REDIS_URL') ?: 'redis://redis:6379';
        $parsed = parse_url($redis_url);
        
        if (!$parsed) {
            throw new Exception("Invalid REDIS_URL format");
        }
        
        $this->redis = new Redis();
        $connected = $this->redis->connect(
            $parsed['host'],
            $parsed['port'] ?? 6379
        );
        
        if (!$connected) {
            throw new Exception("Failed to connect to Redis");
        }
        
        // TODO: Select the appropriate database if specified in the URL
        // The URL path may contain a database number like /2
        // You need to extract the database number and select it using Redis SELECT command
        // Redis command: SELECT <database_number>
        
        // Optional: authentication if password is provided
        if (isset($parsed['pass'])) {
            $this->redis->auth($parsed['pass']);
        }
    }
    
    /**
     * Get singleton instance
     */
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    /**
     * Get value from cache
     */
    public function get($key) {
        $value = $this->redis->get($key);
        return $value !== false ? $value : null;
    }
    
    /**
     * Set value in cache with TTL
     */
    public function set($key, $value, $ttl = 300) {
        return $this->redis->setex($key, $ttl, $value);
    }
    
    /**
     * Delete key from cache
     */
    public function delete($key) {
        return $this->redis->del($key);
    }
    
    /**
     * Check if key exists in cache
     */
    public function exists($key) {
        return $this->redis->exists($key) > 0;
    }
    
    /**
     * Test Redis connection
     */
    public function ping() {
        try {
            return $this->redis->ping() === '+PONG';
        } catch (Exception $e) {
            return false;
        }
    }
}

// Create global instance for use in endpoints
$cache = CacheManager::getInstance();
