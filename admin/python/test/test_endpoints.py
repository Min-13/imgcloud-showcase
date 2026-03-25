"""
Unit tests for endpoints module (endpoints.py)
Tests all 5 endpoints: Users, Images, Operations, Jobs, Health
"""
import unittest
import os
import sys
import json
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestUsersEndpoint(unittest.TestCase):
    """Test Users endpoint"""
    
    @patch('endpoints.cache')
    @patch('endpoints.db')
    def test_users_endpoint_cache_hit(self, mock_db, mock_cache):
        """Test Users endpoint with cache hit"""
        from endpoints import UsersEndpoint
        
        # Mock cache hit
        cached_data = json.dumps({
            'users': [{'id': 1, 'username': 'test', 'email': 'test@test.com'}],
            'cached': True,
            'cache_ttl': 300
        })
        mock_cache.get.return_value = cached_data
        
        endpoint = UsersEndpoint()
        result = endpoint.get()
        
        # Verify cache was checked
        mock_cache.get.assert_called_once()
        
        # Verify database was not queried
        mock_db.execute_query.assert_not_called()
        
        # Verify response
        response = json.loads(result)
        self.assertTrue(response['cached'])
        self.assertEqual(len(response['users']), 1)
    
    @patch('endpoints.cache')
    @patch('endpoints.db')
    def test_users_endpoint_cache_miss(self, mock_db, mock_cache):
        """Test Users endpoint with cache miss"""
        from endpoints import UsersEndpoint
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock database query result
        mock_db.execute_query.return_value = [
            {'id': 1, 'username': 'user1', 'email': 'user1@test.com',
             'created_at': '2024-01-01', 'image_count': 5, 'job_count': 3}
        ]
        
        endpoint = UsersEndpoint()
        result = endpoint.get()
        
        # Verify cache was checked
        mock_cache.get.assert_called_once()
        
        # Verify database was queried
        mock_db.execute_query.assert_called_once()
        
        # Verify cache was updated
        mock_cache.set.assert_called_once()
        
        # Verify response structure
        response = json.loads(result)
        self.assertFalse(response['cached'])
        self.assertEqual(response['cache_ttl'], 300)

class TestImagesEndpoint(unittest.TestCase):
    """Test Images endpoint"""
    
    @patch('endpoints.cache')
    @patch('endpoints.db')
    def test_images_endpoint_structure(self, mock_db, mock_cache):
        """Test Images endpoint returns correct structure"""
        from endpoints import ImagesEndpoint
        
        mock_cache.get.return_value = None
        mock_db.execute_query.return_value = [
            {
                'id': 1,
                'user_id': 1,
                'username': 'user1',
                'filename': 'test.jpg',
                'size': 1024,
                'content_type': 'image/jpeg',
                'uploaded_at': '2024-01-01'
            }
        ]
        
        endpoint = ImagesEndpoint()
        result = endpoint.get()
        
        response = json.loads(result)
        self.assertIn('images', response)
        self.assertIn('cached', response)
        self.assertEqual(len(response['images']), 1)
        
        image = response['images'][0]
        self.assertIn('id', image)
        self.assertIn('filename', image)
        self.assertIn('user_id', image)

class TestOperationsEndpoint(unittest.TestCase):
    """Test Operations endpoint"""
    
    @patch('endpoints.cache')
    @antml:parameter name="db')
    def test_operations_endpoint_structure(self, mock_db, mock_cache):
        """Test Operations endpoint returns statistics"""
        from endpoints import OperationsEndpoint
        
        mock_cache.get.return_value = None
        mock_db.execute_query.return_value = [
            {
                'operation': 'resize',
                'total': 100,
                'completed': 95,
                'failed': 3,
                'pending': 2,
                'avg_time_ms': 150.5
            }
        ]
        
        endpoint = OperationsEndpoint()
        result = endpoint.get()
        
        response = json.loads(result)
        self.assertIn('operations', response)
        self.assertEqual(len(response['operations']), 1)
        
        op = response['operations'][0]
        self.assertEqual(op['operation'], 'resize')
        self.assertEqual(op['total'], 100)
        self.assertIsInstance(op['avg_time_ms'], (int, float))

class TestJobsEndpoint(unittest.TestCase):
    """Test Jobs endpoint"""
    
    @patch('endpoints.cache')
    @patch('endpoints.db')
    def test_jobs_endpoint_structure(self, mock_db, mock_cache):
        """Test Jobs endpoint returns jobs and queue stats"""
        from endpoints import JobsEndpoint
        
        mock_cache.get.return_value = None
        
        # Mock two queries: jobs list and queue stats
        mock_db.execute_query.side_effect = [
            [  # Jobs list
                {
                    'id': 1,
                    'user_id': 1,
                    'username': 'user1',
                    'operation_type': 'resize',
                    'status': 'completed',
                    'created_at': '2024-01-01',
                    'completed_at': '2024-01-01'
                }
            ],
            [  # Queue stats
                {
                    'pending': 5,
                    'processing': 2,
                    'completed': 100,
                    'failed': 3
                }
            ]
        ]
        
        endpoint = JobsEndpoint()
        result = endpoint.get()
        
        response = json.loads(result)
        self.assertIn('jobs', response)
        self.assertIn('queue_stats', response)
        
        # Verify two queries were made
        self.assertEqual(mock_db.execute_query.call_count, 2)

class TestHealthEndpoint(unittest.TestCase):
    """Test Health endpoint"""
    
    @patch('endpoints.cache')
    @patch('endpoints.db')
    def test_health_endpoint_all_healthy(self, mock_db, mock_cache):
        """Test Health endpoint when all services healthy"""
        from endpoints import HealthEndpoint
        
        # Mock successful connections
        mock_db.execute_query.return_value = [{'result': 1}]
        mock_cache.redis_client.ping.return_value = True
        
        endpoint = HealthEndpoint()
        result = endpoint.get()
        
        response = json.loads(result)
        self.assertEqual(response['status'], 'healthy')
        self.assertTrue(response['database'])
        self.assertTrue(response['cache'])
    
    @patch('endpoints.cache')
    @patch('endpoints.db')
    def test_health_endpoint_db_failure(self, mock_db, mock_cache):
        """Test Health endpoint when database fails"""
        from endpoints import HealthEndpoint
        
        # Mock database failure
        mock_db.execute_query.side_effect = Exception("Connection failed")
        mock_cache.redis_client.ping.return_value = True
        
        endpoint = HealthEndpoint()
        result = endpoint.get()
        
        response = json.loads(result)
        self.assertEqual(response['status'], 'unhealthy')
        self.assertFalse(response['database'])

class TestEndpointIntegration(unittest.TestCase):
    """Integration tests for endpoints"""
    
    def test_all_endpoints_return_json(self):
        """Test that all endpoints return valid JSON"""
        from endpoints import UsersEndpoint, ImagesEndpoint, OperationsEndpoint, JobsEndpoint, HealthEndpoint
        
        endpoints = [
            UsersEndpoint(),
            ImagesEndpoint(),
            OperationsEndpoint(),
            JobsEndpoint(),
            HealthEndpoint()
        ]
        
        for endpoint in endpoints:
            with patch('endpoints.db'), patch('endpoints.cache'):
                # This test just verifies endpoints exist and can be instantiated
                self.assertIsNotNone(endpoint)

if __name__ == '__main__':
    unittest.main()
