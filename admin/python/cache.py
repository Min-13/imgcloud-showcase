"""
Redis cache module for LAB05
Provides simple caching interface with TTL support
"""

import redis
import os
from urllib.parse import urlparse

class CacheManager:
    """Redis cache manager"""
    
    def __init__(self):
        """Initialize Redis connection from REDIS_URL environment variable"""
        redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # TODO: Select the appropriate database if specified in the URL
        # The redis_url may include a database number like redis://host:port/2
        # You need to parse the database number from the URL and select it using Redis SELECT command
        # Redis command: SELECT <database_number>
        parsed = urlparse(redis_url)
        if parsed.path and parsed.path != "/":
            try:
                db_number = int(parsed.path.lstrip("/"))
                self.redis_client.execute_command("SELECT", db_number)
            except ValueError:
                raise ValueError("Invalid Redis database number in REDIS_URL")

    def get(self, key):
        """
        Get value from cache
        
        Args:
            key: Cache key string
            
        Returns:
            Value string or None if not found
        """
        return self.redis_client.get(key)
    
    def set(self, key, value, ttl=300):
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key string
            value: Value string to cache
            ttl: Time to live in seconds (default: 300)
            
        Returns:
            True if successful
        """
        return self.redis_client.setex(key, ttl, value)
    
    def delete(self, key):
        """
        Delete key from cache
        
        Args:
            key: Cache key string
            
        Returns:
            Number of keys deleted
        """
        return self.redis_client.delete(key)
    
    def exists(self, key):
        """
        Check if key exists in cache
        
        Args:
            key: Cache key string
            
        Returns:
            True if key exists
        """
        return self.redis_client.exists(key) > 0
    
    def ping(self):
        """
        Test Redis connection
        
        Returns:
            True if connection is alive
        """
        try:
            return self.redis_client.ping()
        except Exception:
            return False


# Global cache instance for compatibility with endpoints.py
cache = CacheManager()
