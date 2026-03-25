"""
Schema validation tests for admin endpoints.
Ensures all endpoints return the exact field names expected by admin.html
"""
import unittest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestSchemaValidation(unittest.TestCase):
    """
    Tests that validate endpoint responses match admin.html expectations.
    These tests prevent "undefined" values in the UI.
    """
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/test'
        os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
    
    @patch('endpoints.db')
    @patch('endpoints.cache')
    def test_operations_endpoint_schema(self, mock_cache, mock_db):
        """
        Test that Operations endpoint returns fields expected by admin.html:
        - operation (string)
        - count (int)
        - completed_count (int)
        - failed_count (int)
        - avg_time_ms (float)
        """
        from endpoints import OperationsEndpoint
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock database response
        mock_db.execute_query.return_value = [
            {
                'operation_type': 'resize',
                'total_count': 100,
                'completed_count': 95,
                'failed_count': 5,
                'pending_count': 0,
                'avg_time_ms': 123.45
            }
        ]
        
        # Call endpoint
        response = OperationsEndpoint.get()
        data = response.get_json()
        
        # Verify response structure
        self.assertIn('operations', data)
        self.assertIsInstance(data['operations'], list)
        
        if len(data['operations']) > 0:
            op = data['operations'][0]
            
            # CRITICAL: These exact field names are used in admin.html line 414-418
            self.assertIn('operation', op, "Missing 'operation' field - will show undefined in UI")
            self.assertIn('count', op, "Missing 'count' field - will show undefined in UI") 
            self.assertIn('completed_count', op, "Missing 'completed_count' field - will show undefined in UI")
            self.assertIn('failed_count', op, "Missing 'failed_count' field - will show undefined in UI")
            self.assertIn('avg_time_ms', op, "Missing 'avg_time_ms' field - will show undefined in UI")
            
            # Verify types
            self.assertIsInstance(op['operation'], str)
            self.assertIsInstance(op['count'], int)
            self.assertIsInstance(op['completed_count'], int)
            self.assertIsInstance(op['failed_count'], int)
            self.assertIsInstance(op['avg_time_ms'], (int, float))
    
    @patch('endpoints.db')
    @patch('endpoints.cache')
    def test_jobs_endpoint_schema(self, mock_cache, mock_db):
        """
        Test that Jobs endpoint returns fields expected by admin.html:
        
        For jobs array (line 462-473):
        - id (int)
        - username (string)
        - operation (string)
        - status (string)
        - created_at (ISO string)
        - completed_at (ISO string or null)
        
        For queue_stats (line 446-449):
        - pending (int)
        - processing (int)
        - completed (int)
        - failed (int)
        """
        from endpoints import JobsEndpoint
        from datetime import datetime
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock database responses
        mock_db.execute_query.side_effect = [
            # Jobs query
            [
                {
                    'id': 1,
                    'user_id': 123,
                    'username': 'testuser',
                    'operation': 'resize',
                    'status': 'completed',
                    'created_at': datetime(2024, 1, 1, 12, 0, 0),
                    'completed_at': datetime(2024, 1, 1, 12, 5, 0)
                }
            ],
            # Stats query
            [
                {'status': 'pending', 'count': 5},
                {'status': 'processing', 'count': 2},
                {'status': 'completed', 'count': 100},
                {'status': 'failed', 'count': 3}
            ]
        ]
        
        # Call endpoint
        response = JobsEndpoint.get()
        data = response.get_json()
        
        # Verify response structure
        self.assertIn('jobs', data)
        self.assertIn('queue_stats', data)
        
        # Verify jobs array schema
        if len(data['jobs']) > 0:
            job = data['jobs'][0]
            
            # CRITICAL: These exact field names are used in admin.html line 467-472
            self.assertIn('id', job, "Missing 'id' field - will show undefined in UI")
            self.assertIn('username', job, "Missing 'username' field - will show undefined in UI")
            self.assertIn('operation', job, "Missing 'operation' field - will show undefined in UI")
            self.assertIn('status', job, "Missing 'status' field - will show undefined in UI")
            self.assertIn('created_at', job, "Missing 'created_at' field - will show undefined in UI")
            self.assertIn('completed_at', job, "Missing 'completed_at' field - will show undefined in UI")
            
            # Verify types
            self.assertIsInstance(job['id'], int)
            self.assertIsInstance(job['username'], str)
            self.assertIsInstance(job['operation'], str)
            self.assertIsInstance(job['status'], str)
            self.assertIsInstance(job['created_at'], str)  # Should be ISO format
            self.assertTrue(job['completed_at'] is None or isinstance(job['completed_at'], str))
        
        # Verify queue_stats schema
        stats = data['queue_stats']
        
        # CRITICAL: These exact field names are used in admin.html line 446-449
        self.assertIn('pending', stats, "Missing 'pending' field - will show undefined in UI")
        self.assertIn('processing', stats, "Missing 'processing' field - will show undefined in UI")
        self.assertIn('completed', stats, "Missing 'completed' field - will show undefined in UI")
        self.assertIn('failed', stats, "Missing 'failed' field - will show undefined in UI")
        
        # Verify types
        self.assertIsInstance(stats['pending'], int)
        self.assertIsInstance(stats['processing'], int)
        self.assertIsInstance(stats['completed'], int)
        self.assertIsInstance(stats['failed'], int)
    
    @patch('endpoints.db')
    @patch('endpoints.cache')
    def test_users_endpoint_schema(self, mock_cache, mock_db):
        """Test that Users endpoint returns expected fields"""
        from endpoints import UsersEndpoint
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock database response
        mock_db.execute_query.return_value = [
            {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'created_at': '2024-01-01T12:00:00',
                'image_count': 10,
                'job_count': 5
            }
        ]
        
        # Call endpoint
        response = UsersEndpoint.get()
        data = response.get_json()
        
        # Verify response structure
        self.assertIn('users', data)
        
        if len(data['users']) > 0:
            user = data['users'][0]
            
            # Verify expected fields exist
            self.assertIn('id', user)
            self.assertIn('username', user)
            self.assertIn('email', user)
            self.assertIn('created_at', user)
            self.assertIn('image_count', user)
            self.assertIn('job_count', user)
    
    @patch('endpoints.db')
    @patch('endpoints.cache')
    def test_images_endpoint_schema(self, mock_cache, mock_db):
        """
        Test that Images endpoint returns fields expected by admin.html:
        
        Fields used in admin.html lines 371-378:
        - img.id
        - img.username
        - img.original_filename (line 376)
        - img.file_size (line 372)
        - img.upload_date (line 371)
        - img.content_type (line 378)
        """
        from endpoints import ImagesEndpoint
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock database response with CORRECT field names
        mock_db.execute_query.return_value = [
            {
                'id': 1,
                'user_id': 123,
                'username': 'testuser',
                'original_filename': 'test.jpg',
                'file_size': 1024,
                'content_type': 'image/jpeg',
                'upload_date': '2024-01-01T12:00:00'
            }
        ]
        
        # Call endpoint
        response = ImagesEndpoint.get()
        data = response.get_json()
        
        # Verify response structure
        self.assertIn('images', data)
        
        if len(data['images']) > 0:
            image = data['images'][0]
            
            # CRITICAL: These exact field names are used in admin.html lines 371-378
            self.assertIn('id', image, "Missing 'id' field")
            self.assertIn('username', image, "Missing 'username' field")
            self.assertIn('original_filename', image, "Missing 'original_filename' field - will show undefined in UI (line 376)")
            self.assertIn('file_size', image, "Missing 'file_size' field - will show undefined in UI (line 372)")
            self.assertIn('upload_date', image, "Missing 'upload_date' field - will show undefined in UI (line 371)")
            self.assertIn('content_type', image, "Missing 'content_type' field")
            
            # WRONG FIELD NAMES that should NOT be present
            self.assertNotIn('filename', image, "Field should be 'original_filename' not 'filename'!")
            self.assertNotIn('size', image, "Field should be 'file_size' not 'size'!")
            self.assertNotIn('uploaded_at', image, "Field should be 'upload_date' not 'uploaded_at'!")



if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
