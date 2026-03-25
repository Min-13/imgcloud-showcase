"""
Unit tests for cache module (cache.py)
Tests Redis connection, URL parsing, and cache operations
"""
import unittest
import os
import sys
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestCacheConnection(unittest.TestCase):
    """Test cache connection and operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_redis_url = "redis://localhost:6379/0"
        os.environ['REDIS_URL'] = self.test_redis_url
    
    def tearDown(self):
        """Clean up after tests"""
        if 'REDIS_URL' in os.environ:
            del os.environ['REDIS_URL']
    
    @patch('redis.Redis')
    def test_redis_url_parsing(self, mock_redis):
        """Test REDIS_URL environment variable parsing"""
        from cache import CacheManager
        
        cache = CacheManager()
        self.assertIsNotNone(cache)
    
    @patch('redis.Redis')
    def test_cache_set_operation(self, mock_redis):
        """Test cache set with TTL"""
        from cache import CacheManager
        
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        cache = CacheManager()
        
        # Test set operation
        cache.set('test_key', 'test_value', ttl=300)
        
        # Verify setex was called with key, ttl, value
        mock_redis_instance.setex.assert_called_once()
        args = mock_redis_instance.setex.call_args[0]
        self.assertEqual(args[0], 'test_key')
        self.assertEqual(args[1], 300)
        self.assertEqual(args[2], 'test_value')
    
    @patch('redis.Redis')
    def test_cache_get_operation(self, mock_redis):
        """Test cache get operation"""
        from cache import CacheManager
        
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = b'test_value'
        mock_redis.return_value = mock_redis_instance
        
        cache = CacheManager()
        
        # Test get operation
        value = cache.get('test_key')
        
        mock_redis_instance.get.assert_called_once_with('test_key')
        self.assertEqual(value, 'test_value')
    
    @patch('redis.Redis')
    def test_cache_get_miss(self, mock_redis):
        """Test cache get when key doesn't exist"""
        from cache import CacheManager
        
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance
        
        cache = CacheManager()
        
        value = cache.get('nonexistent_key')
        self.assertIsNone(value)
    
    @patch('redis.Redis')
    def test_cache_delete_operation(self, mock_redis):
        """Test cache delete operation"""
        from cache import CacheManager
        
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        cache = CacheManager()
        
        # Test delete operation
        cache.delete('test_key')
        
        mock_redis_instance.delete.assert_called_once_with('test_key')
    
    @patch('redis.Redis')
    def test_cache_json_serialization(self, mock_redis):
        """Test that cache handles JSON serialization"""
        from cache import CacheManager
        import json
        
        mock_redis_instance = MagicMock()
        test_data = {'id': 1, 'name': 'test'}
        mock_redis_instance.get.return_value = json.dumps(test_data).encode('utf-8')
        mock_redis.return_value = mock_redis_instance
        
        cache = CacheManager()
        
        # Store JSON
        cache.set('json_key', json.dumps(test_data))
        
        # Retrieve and parse
        value = cache.get('json_key')
        retrieved_data = json.loads(value)
        
        self.assertEqual(retrieved_data, test_data)
    
    @patch('redis.from_url')
    def test_redis_database_selection(self, mock_from_url):
        """Test that Redis SELECT command is executed for non-zero database"""
        from cache import CacheManager
        
        # Mock redis client
        mock_redis_client = MagicMock()
        mock_from_url.return_value = mock_redis_client
        
        # Test with database number in URL
        os.environ['REDIS_URL'] = 'redis://localhost:6379/2'
        
        cache = CacheManager()
        
        # Verify redis.from_url was called
        mock_from_url.assert_called_once()
        
        # Verify the student implementation calls execute_command('SELECT', 2)
        # This ensures proper database selection is implemented
        mock_redis_client.execute_command.assert_called_with('SELECT', 2)

class TestCacheIntegration(unittest.TestCase):
    """Integration tests with real Redis (if available)"""
    
    @unittest.skipUnless(os.getenv('TEST_REDIS_URL'), "Test Redis not configured")
    def test_real_redis_connection(self):
        """Test actual Redis connection"""
        os.environ['REDIS_URL'] = os.getenv('TEST_REDIS_URL')
        from cache import CacheManager
        
        cache = CacheManager()
        
        # Test set and get
        cache.set('test_key', 'test_value', ttl=10)
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')
        
        # Clean up
        cache.delete('test_key')

if __name__ == '__main__':
    unittest.main()
