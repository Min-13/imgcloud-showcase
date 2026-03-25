"""
Database connection module for LAB05
Provides connection pooling using psycopg2 ThreadedConnectionPool
"""

from urllib.parse import urlparse
from contextlib import contextmanager
import os
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


# Global singleton instance
_db_pool_instance = None


class DatabasePool:
    """Database connection pool manager"""
    
    def __init__(self):
        """Initialize connection pool from DATABASE_URL environment variable"""
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        parsed = urlparse(db_url)
        
        self.connection_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        
        # TODO: Pre-create some connections for the pool
        # Create 3 initial connections to warm up the pool and test connectivity
        # Use self.connection_pool.getconn() to get a connection from the pool
	# Use self.connection_pool.putconn(conn) to return a connection to the pool
        conns = []
        try:
            for _ in range(3):
                conn = self.connection_pool.getconn()
                conns.append(conn)
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
                cur.close()
        finally:
            for conn in conns:
                self.connection_pool.putconn(conn)

    def get_connection(self):
        """Get a connection from the pool"""
        return self.connection_pool.getconn()
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        self.connection_pool.putconn(conn)
    
    def close_all(self):
        """Close all connections in the pool"""
        self.connection_pool.closeall()


def get_db_pool():
    """Get or create the singleton DatabasePool instance"""
    global _db_pool_instance
    if _db_pool_instance is None:
        _db_pool_instance = DatabasePool()
    return _db_pool_instance


@contextmanager
def get_db_cursor(dict_cursor=True):
    """
    Context manager for database cursors
    Automatically handles connection retrieval and cleanup
    
    Args:
        dict_cursor: If True, returns RealDictCursor (default), else regular cursor
    """
    db_pool = get_db_pool()
    conn = db_pool.get_connection()
    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor) if dict_cursor else conn.cursor()
        yield cursor
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        db_pool.return_connection(conn)


def execute_query(query, params=None, dict_cursor=True):
    """
    Execute a query and return all results
    
    Args:
        query: SQL query string with %s placeholders
        params: Tuple of parameters for the query
        dict_cursor: If True, returns dict results
        
    Returns:
        List of rows (dicts if dict_cursor=True)
    """
    with get_db_cursor(dict_cursor=dict_cursor) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchall()


def execute_query_one(query, params=None, dict_cursor=True):
    """
    Execute a query and return one result
    
    Args:
        query: SQL query string with %s placeholders
        params: Tuple of parameters for the query
        dict_cursor: If True, returns dict result
        
    Returns:
        Single row (dict if dict_cursor=True) or None
    """
    with get_db_cursor(dict_cursor=dict_cursor) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


# Wrapper class to match the interface expected by endpoints.py
class DatabaseConnection:
    """Wrapper to provide db.execute_query() and db.connection_pool interface"""
    
    def __init__(self):
        # Initialize pool on first access
        self._pool = None
    
    @property
    def connection_pool(self):
        """Get the connection pool (for health check)"""
        if self._pool is None:
            self._pool = get_db_pool()
        return self._pool.connection_pool
    
    def execute_query(self, query, params=None):
        """Execute query and return results"""
        return execute_query(query, params)


# Global db instance for compatibility with endpoints.py
db = DatabaseConnection()
