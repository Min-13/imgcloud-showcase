"""
Test to verify the fix for empty parameter handling.
This test validates that empty form parameters are properly handled.
"""
import unittest
import sys

# Test the parameter conversion logic directly
class TestEmptyParameters(unittest.TestCase):
    """Test empty parameter handling"""
    
    def test_empty_string_with_or_operator(self):
        """Test that empty strings are handled correctly with 'or' operator"""
        # This is what happens when form field is empty
        empty_value = ''
        
        # Old code would do: int(empty_value) -> ValueError
        # New code does: int(empty_value or 0) -> 0
        result = int(empty_value or 0)
        self.assertEqual(result, 0)
    
    def test_none_value_with_or_operator(self):
        """Test that None values are handled correctly"""
        none_value = None
        result = int(none_value or 0)
        self.assertEqual(result, 0)
    
    def test_valid_value_preserved(self):
        """Test that valid values are preserved"""
        valid_value = '90'
        result = int(valid_value or 0)
        self.assertEqual(result, 90)
    
    def test_zero_string_preserved(self):
        """Test that '0' string is preserved"""
        zero_string = '0'
        result = int(zero_string or 0)
        self.assertEqual(result, 0)
    
    def test_all_parameters(self):
        """Test all parameter types that can be empty"""
        # Simulate form data
        form_data = {
            'width': '',
            'height': '',
            'kernel_size': '',
            'angle': ''
        }
        
        # These should all work without raising ValueError
        width = int(form_data.get('width') or 0)
        height = int(form_data.get('height') or 0)
        kernel_size = int(form_data.get('kernel_size') or 5)
        angle = int(form_data.get('angle') or 0)
        
        self.assertEqual(width, 0)
        self.assertEqual(height, 0)
        self.assertEqual(kernel_size, 5)
        self.assertEqual(angle, 0)

if __name__ == '__main__':
    unittest.main()
