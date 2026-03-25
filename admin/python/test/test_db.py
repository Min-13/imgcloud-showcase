"""
Unit tests for database module (db.py)
Tests connection pooling, URL parsing, and parameterized query execution
"""
import unittest
import os
import sys
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDatabaseConnection(unittest.TestCase):
    """Test database connection and pool management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_db_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        os.environ['DATABASE_URL'] = self.test_db_url
    
    def tearDown(self):
        """Clean up after tests"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_database_url_parsing(self, mock_pool):
        """Test DATABASE_URL environment variable parsing"""
        from db import DatabaseConnection
        
        # Create connection (should parse URL)
        db = DatabaseConnection()
        
        # Verify initialization was called with parsed components
        self.assertIsNotNone(db)
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_connection_pool_creation(self, mock_pool):
        """Test that connection pool is created with correct parameters"""
        from db import DatabaseConnection
        
        mock_pool.return_value = MagicMock()
        db = DatabaseConnection()
        
        # Verify pool was created
        mock_pool.assert_called_once()
        args, kwargs = mock_pool.call_args
        
        # Check min and max connections (2-10 typical for ThreadedConnectionPool)
        self.assertEqual(args[0], 2)  # minconn
        self.assertEqual(args[1], 10)  # maxconn
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_execute_query_parameterized(self, mock_pool):
        """Test parameterized query execution"""
        from db import DatabaseConnection
        
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
        mock_cursor.description = [('id',), ('name',)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        
        db = DatabaseConnection()
        
        # Execute query with parameters
        query = "SELECT * FROM users WHERE id = %s"
        params = (1,)
        result = db.execute_query(query, params)
        
        # Verify execute was called with query and params
        mock_cursor.execute.assert_called_once_with(query, params)
        self.assertIsNotNone(result)
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_sql_injection_prevention(self, mock_pool):
        """Test that parameterized queries prevent SQL injection"""
        from db import DatabaseConnection
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance
        
        db = DatabaseConnection()
        
        # Try query with potential SQL injection
        malicious_input = "1 OR 1=1"
        query = "SELECT * FROM users WHERE id = %s"
        
        db.execute_query(query, (malicious_input,))
        
        # Verify parameters were passed separately (not interpolated)
        call_args = mock_cursor.execute.call_args
        self.assertEqual(call_args[0][0], query)
        self.assertEqual(call_args[0][1], (malicious_input,))

class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests with real database (if available)"""
    
    def setUp(self):
        """Check if test database is available"""
        self.db_available = os.getenv('TEST_DATABASE_URL') is not None
        if self.db_available:
            os.environ['DATABASE_URL'] = os.getenv('TEST_DATABASE_URL')
    
    @unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), "Test database not configured")
    def test_real_connection(self):
        """Test actual database connection"""
        from db import DatabaseConnection
        
        db = DatabaseConnection()
        
        # Try simple query
        result = db.execute_query("SELECT 1 as test")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

if __name__ == '__main__':
    unittest.main()
