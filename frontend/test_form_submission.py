"""
Integration test to verify form submission with empty parameters works correctly.
"""
import unittest
from unittest.mock import patch, MagicMock
import io
from PIL import Image
from werkzeug.datastructures import MultiDict
from app import app

class TestFormSubmissionWithEmptyParams(unittest.TestCase):
    """Test form submission with empty parameters"""
    
    def setUp(self):
        """Set up test client and test image"""
        self.app = app.test_client()
        self.app.testing = True
        self.test_image = Image.new('RGB', (100, 100), color='red')
    
    @patch('app.grpc.insecure_channel')
    def test_grayscale_with_empty_parameters(self, mock_channel):
        """Test that grayscale operation works even with empty parameters"""
        # Mock gRPC channel
        mock_channel_instance = MagicMock()
        mock_channel.return_value.__enter__.return_value = mock_channel_instance
        
        # Mock the gRPC response
        mock_response = MagicMock()
        mock_response.error = ''
        mock_response.image_data = b'fake_processed_image'
        
        with patch('app.image_processor_pb2_grpc.ImageProcessorStub') as mock_stub_class:
            mock_stub_instance = MagicMock()
            mock_stub_instance.ProcessImage.return_value = mock_response
            mock_stub_class.return_value = mock_stub_instance
            
            # Create test image
            img_io = io.BytesIO()
            self.test_image.save(img_io, 'PNG')
            img_io.seek(0)
            
            # Submit form with empty angle (simulating hidden field being submitted)
            response = self.app.post('/process', data={
                'operation': 'grayscale',
                'image': (img_io, 'test.png'),
                'angle': '',  # Empty angle field
                'width': '',  # Empty width field
                'height': '', # Empty height field
            }, content_type='multipart/form-data')
            
            # Should succeed, not raise ValueError
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'image/png')
    
    @patch('app.grpc.insecure_channel')
    def test_rotate_with_valid_angle(self, mock_channel):
        """Test that rotate operation works with valid angle parameter"""
        # Mock gRPC setup
        mock_channel_instance = MagicMock()
        mock_channel.return_value.__enter__.return_value = mock_channel_instance
        
        mock_response = MagicMock()
        mock_response.error = ''
        mock_response.image_data = b'fake_rotated_image'
        
        with patch('app.image_processor_pb2_grpc.ImageProcessorStub') as mock_stub_class:
            mock_stub_instance = MagicMock()
            mock_stub_instance.ProcessImage.return_value = mock_response
            mock_stub_class.return_value = mock_stub_instance
            
            # Create test image
            img_io = io.BytesIO()
            self.test_image.save(img_io, 'PNG')
            img_io.seek(0)
            
            # Submit form with valid angle
            response = self.app.post('/process', data={
                'operation': 'rotate',
                'image': (img_io, 'test.png'),
                'angle': '90',
            }, content_type='multipart/form-data')
            
            # Should succeed
            self.assertEqual(response.status_code, 200)
            
            # Verify angle was passed correctly to gRPC
            call_args = mock_stub_instance.ProcessImage.call_args
            request = call_args[0][0]
            self.assertEqual(request.angle, 90)

if __name__ == '__main__':
    unittest.main()
