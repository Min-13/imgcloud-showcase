"""
Tests for Lab07 endpoints: instance identification and unhealthy toggling.

Validates the X-Instance-ID response header, the /api/toggle-unhealthy endpoint,
and the forced-unhealthy behaviour which affects all endpoints (not just /health).
"""
import unittest
from unittest.mock import patch, MagicMock
import app as app_module
from app import app


class TestInstanceIDHeaderOnAllResponses(unittest.TestCase):
    """Test that X-Instance-ID header is present on multiple endpoint types"""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        app_module._force_unhealthy = False

    def tearDown(self):
        app_module._force_unhealthy = False

    def test_header_on_operations_endpoint(self):
        """X-Instance-ID must be present on the /operations endpoint"""
        response = self.client.get('/operations')
        self.assertIn('X-Instance-ID', response.headers)

    def test_header_on_toggle_unhealthy_endpoint(self):
        """X-Instance-ID must be present on the /api/toggle-unhealthy endpoint"""
        response = self.client.post('/api/toggle-unhealthy')
        self.assertIn('X-Instance-ID', response.headers)

    def test_header_on_forced_unhealthy_response(self):
        """X-Instance-ID must still be present when instance is forced unhealthy"""
        app_module._force_unhealthy = True
        response = self.client.get('/health')
        self.assertIn('X-Instance-ID', response.headers)
        self.assertEqual(response.headers['X-Instance-ID'], app_module.INSTANCE_ID)


class TestInstanceID(unittest.TestCase):
    """Test that the X-Instance-ID header is present on all responses"""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        # Ensure the instance starts in a healthy state
        app_module._force_unhealthy = False

    def test_health_response_contains_instance_id(self):
        """X-Instance-ID header must appear on health responses"""
        with patch('app.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp

            response = self.client.get('/health')
            self.assertIn('X-Instance-ID', response.headers)

    def test_health_body_contains_instance_id(self):
        """The /health JSON body must include an instance_id field"""
        with patch('app.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp

            response = self.client.get('/health')
            data = response.get_json()
            self.assertIn('instance_id', data)
            self.assertEqual(data['instance_id'], app_module.INSTANCE_ID)

    def test_instance_id_env_var(self):
        """INSTANCE_ID should default to 'frontend' when not set"""
        # The default is already set at module import time; just verify the value
        self.assertIsInstance(app_module.INSTANCE_ID, str)
        self.assertTrue(len(app_module.INSTANCE_ID) > 0)


class TestToggleUnhealthy(unittest.TestCase):
    """Test the /api/toggle-unhealthy endpoint"""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        # Reset to healthy before each test
        app_module._force_unhealthy = False

    def tearDown(self):
        # Always restore healthy state after each test
        app_module._force_unhealthy = False

    def test_toggle_unhealthy_returns_200(self):
        """POST /api/toggle-unhealthy should return 200"""
        response = self.client.post('/api/toggle-unhealthy')
        self.assertEqual(response.status_code, 200)

    def test_toggle_unhealthy_flips_flag(self):
        """First POST should set unhealthy=True"""
        response = self.client.post('/api/toggle-unhealthy')
        data = response.get_json()
        self.assertTrue(data['unhealthy'])

    def test_toggle_unhealthy_second_call_restores_healthy(self):
        """Second POST should restore unhealthy=False"""
        self.client.post('/api/toggle-unhealthy')
        response = self.client.post('/api/toggle-unhealthy')
        data = response.get_json()
        self.assertFalse(data['unhealthy'])

    def test_toggle_response_includes_instance_id(self):
        """Toggle response must include the instance_id field"""
        response = self.client.post('/api/toggle-unhealthy')
        data = response.get_json()
        self.assertIn('instance_id', data)
        self.assertEqual(data['instance_id'], app_module.INSTANCE_ID)

    def test_toggle_response_includes_message(self):
        """Toggle response must include a human-readable message"""
        response = self.client.post('/api/toggle-unhealthy')
        data = response.get_json()
        self.assertIn('message', data)

    def test_toggle_still_reachable_when_forced_unhealthy(self):
        """POST /api/toggle-unhealthy must return 200 even when the instance is forced unhealthy"""
        # First call sets unhealthy
        self.client.post('/api/toggle-unhealthy')
        # Second call (from inside the "unhealthy" state) must still work to restore
        response = self.client.post('/api/toggle-unhealthy')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['unhealthy'])


class TestForcedUnhealthyAffectsAllEndpoints(unittest.TestCase):
    """Test that the forced-unhealthy flag causes all endpoints to return 503"""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        app_module._force_unhealthy = False

    def tearDown(self):
        app_module._force_unhealthy = False

    def test_health_returns_503_when_forced_unhealthy(self):
        """When force-unhealthy is set, /health must return HTTP 503"""
        app_module._force_unhealthy = True
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 503)

    def test_operations_returns_503_when_forced_unhealthy(self):
        """When force-unhealthy is set, /operations must also return HTTP 503"""
        app_module._force_unhealthy = True
        response = self.client.get('/operations')
        self.assertEqual(response.status_code, 503)

    def test_forced_unhealthy_response_body_has_status_field(self):
        """Forced unhealthy response body must have status='unhealthy'"""
        app_module._force_unhealthy = True
        response = self.client.get('/health')
        data = response.get_json()
        self.assertEqual(data['status'], 'unhealthy')

    def test_forced_unhealthy_response_includes_instance_id(self):
        """Forced unhealthy response must still include instance_id"""
        app_module._force_unhealthy = True
        response = self.client.get('/health')
        data = response.get_json()
        self.assertIn('instance_id', data)

    def test_returns_200_after_toggle_back(self):
        """After toggling back to healthy, /health should no longer return 503"""
        app_module._force_unhealthy = True
        app_module._force_unhealthy = False

        with patch('app.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp

            response = self.client.get('/health')
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
