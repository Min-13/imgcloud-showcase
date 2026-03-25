"""
Test suite for the image processing frontend service.
These tests verify the frontend API gateway functionality.
Note: These are unit tests that mock the processor service.
For integration tests with the actual C++ processor, use docker-compose.
"""
import unittest
import io
from unittest.mock import patch, MagicMock
from PIL import Image
from app import app


class TestFrontendService(unittest.TestCase):
    """Test frontend API gateway functions"""
    
    def setUp(self):
        """Set up test client and create test image"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Create a simple test image (100x100 red square)
        self.test_image = Image.new('RGB', (100, 100), color='red')
    
    @patch('app.requests.get')
    def test_health_endpoint_with_healthy_processor(self, mock_get):
        """Test health endpoint when processor is healthy"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['processor'], 'healthy')
    
    @patch('app.requests.get')
    def test_health_endpoint_with_unavailable_processor(self, mock_get):
        """Test health endpoint when processor is unavailable"""
        mock_get.side_effect = Exception("Connection refused")
        
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'degraded')
        self.assertEqual(data['processor'], 'unavailable')
    
    def test_root_endpoint(self):
        """Test root endpoint returns index.html"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')
        # Verify the response contains HTML content
        self.assertIn(b'<!DOCTYPE html>', response.data)
        self.assertIn(b'Image Processing Service', response.data)
    
    def test_operations_endpoint(self):
        """Test operations listing endpoint"""
        response = self.app.get('/operations')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('operations', data)
        # Should include: resize, grayscale, blur, edge_detection, rotate, mirror
        self.assertEqual(len(data['operations']), 6)
        
        # Verify operation names
        operation_names = [op['name'] for op in data['operations']]
        self.assertIn('resize', operation_names)
        self.assertIn('grayscale', operation_names)
        self.assertIn('blur', operation_names)
        self.assertIn('edge_detection', operation_names)
        self.assertIn('rotate', operation_names)
        self.assertIn('mirror', operation_names)
    
    @patch('app.requests.post')
    def test_process_endpoint_forwards_to_processor(self, mock_post):
        """Test that process endpoint forwards requests to processor"""
        # Create a mock response from processor
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_post.return_value = mock_response
        
        # Create test image data
        img_io = io.BytesIO()
        self.test_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        # Send request to frontend
        response = self.app.post('/process', data={
            'operation': 'grayscale',
            'image': (img_io, 'test.png')
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'image/png')
        
        # Verify the request was forwarded to processor
        mock_post.assert_called_once()
    
    @patch('app.requests.post')
    def test_process_endpoint_handles_processor_unavailable(self, mock_post):
        """Test process endpoint handles processor connection errors"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Create test image data
        img_io = io.BytesIO()
        self.test_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        response = self.app.post('/process', data={
            'operation': 'grayscale',
            'image': (img_io, 'test.png')
        })
        
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()
