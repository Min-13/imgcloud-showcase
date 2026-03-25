"""
LAB05 Solution - Endpoint implementations
Only Users and Images endpoints are in the solutions directory.
Operations and Jobs are provided to students in the admin/python/ directory.
"""
from flask import jsonify
from db import db
from cache import cache
import os
import json

# Configuration
CACHE_TTL = int(os.environ.get('CACHE_TTL', 300))


class UsersEndpoint:
    """
    TODO: Implement the Users endpoint.
    
    Requirements:
    - Cache key: 'admin:users'
    - Check cache first, return cached data if found
    - Query database for all users with image_count and job_count
    - Use LEFT JOIN to include users with zero images/jobs
    - Use COUNT(DISTINCT ...) to avoid double-counting
    - Format response with 'users' array, 'cached' flag, 'cache_ttl'
    - Store in cache with TTL of 300 seconds
    
    Required fields in each user object:
    - id, username, email, created_at, image_count, job_count
    
    See LAB05-QUERIES.md for SQL query requirements.
    Study the OperationsEndpoint below for the complete pattern.
    """
    
    @staticmethod
    def get():
        """Get list of all users with statistics."""
        # TODO: Implement this endpoint
        # 1. Check cache with key 'admin:users'
        # 2. If cache hit, return cached data with cached=True
        # 3. If cache miss:
        #    - Write SQL query to get users with image_count and job_count
        #    - Execute query: rows = db.execute_query(query)
        #    - Convert rows to list of dicts with required fields
        #    - Create response dict with users, cached=False, cache_ttl=300
        #    - Store in cache: cache.set(cache_key, json.dumps(response), ttl=300)
        #    - Return jsonify(response)

        cache_key = 'admin:users'

        cached_data = cache.get(cache_key)
        if cached_data:
            response = json.loads(cached_data)
            response['cached'] = True
            return jsonify(response)

        query = """
            SELECT
                u.id,
                u.username,
                NULL::text AS email,
                u.created_at,
                COUNT(DISTINCT i.id) AS image_count,
                COUNT(DISTINCT j.id) AS job_count
            FROM users u
            LEFT JOIN images i ON i.user_id = u.id
            LEFT JOIN jobs j ON j.user_id = u.id
            GROUP BY u.id, u.username, u.created_at
            ORDER BY u.created_at DESC
        """

        rows = db.execute_query(query)

        users_list = []
        for row in rows:
            users_list.append({
                'id': int(row['id']) if row.get('id') is not None else None,
                'username': row.get('username'),
                'email': row.get('email'),
                'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                'image_count': int(row['image_count']) if row.get('image_count') is not None else 0,
                'job_count': int(row['job_count']) if row.get('job_count') is not None else 0
            })

        response = {
            'users': users_list,
            'cached': False,
            'cache_ttl': CACHE_TTL 
        }

        cache.set(cache_key, json.dumps(response), ttl=CACHE_TTL)

        return jsonify(response)


class ImagesEndpoint:
    """
    TODO: Implement the Images endpoint.
    
    Requirements:
    - Cache key: 'admin:images'
    - Check cache first, return cached data if found
    - Query database for recent images (limit 100)
    - Join with users table to get username
    - Order by upload date (newest first)
    - Format response with 'images' array, 'total' count, 'cached' flag, 'cache_ttl'
    - Store in cache with TTL of 300 seconds
    
    Required fields in each image object (use EXACT database column names):
    - id, user_id, username, original_filename, file_size, content_type, upload_date
    
    CRITICAL: Use database column names as-is in JSON (admin.html expects these exact names):
    - original_filename (NOT "filename")
    - file_size (NOT "size")
    - upload_date (NOT "uploaded_at")
    
    See LAB05-QUERIES.md for SQL query requirements.
    Study the OperationsEndpoint below for the complete pattern.
    """
    
    @staticmethod
    def get():
        """Get list of recent images."""
        # TODO: Implement this endpoint
        # 1. Check cache with key 'admin:images'
        # 2. If cache hit, return cached data with cached=True
        # 3. If cache miss:
        #    - Write SQL query to get images with user information
        #    - Execute query: rows = db.execute_query(query)
        #    - Convert rows to list of dicts (map database columns to JSON fields!)
        #    - Create response dict with images, total, cached=False, cache_ttl=300
        #    - Store in cache: cache.set(cache_key, json.dumps(response), ttl=300)
        #    - Return jsonify(response)
        cache_key = 'admin:images'

        cached_data = cache.get(cache_key)
        if cached_data:
            response = json.loads(cached_data)
            response['cached'] = True
            return jsonify(response)

        images_query = """
            SELECT
                i.id,
                i.user_id,
                u.username,
                i.original_filename,
                i.file_size,
                i.content_type,
                i.upload_date
            FROM images i
            INNER JOIN users u ON u.id = i.user_id
            ORDER BY i.upload_date DESC
            LIMIT 100
        """

        total_query = """
            SELECT COUNT(*) AS total
            FROM images
        """

        image_rows = db.execute_query(images_query)
        total_rows = db.execute_query(total_query)
        total = int(total_rows[0]['total']) if total_rows and total_rows[0].get('total') is not None else 0

        images_list = []
        for row in image_rows:
            images_list.append({
                'id': int(row['id']) if row.get('id') is not None else None,
                'user_id': int(row['user_id']) if row.get('user_id') is not None else None,
                'username': row.get('username'),
                'original_filename': row.get('original_filename'),
                'file_size': int(row['file_size']) if row.get('file_size') is not None else 0,
                'content_type': row.get('content_type'),
                'upload_date': row['upload_date'].isoformat() if row.get('upload_date') else None
            })

        # Format response
        response = {
            'images': images_list,
            'total': total,
            'cached': False,
            'cache_ttl': CACHE_TTL
        }
        
        # Store in cache
        cache.set(cache_key, json.dumps(response), ttl=CACHE_TTL)
        
        return jsonify(response)

# The following endpoints are provided to students as complete examples
# They are included here so the solution can run standalone


class OperationsEndpoint:
    """Handles /api/operations endpoint. This endpoint is provided as an example."""
    
    @staticmethod
    def get():
        """
        Get statistics about image processing operations.
        Study this implementation to understand the pattern for UsersEndpoint and ImagesEndpoint.
        """
        cache_key = 'admin:operations'
        
        # Check cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            response = json.loads(cached_data)
            response['cached'] = True
            return jsonify(response)
        
        # Cache miss - query database
        query = """
            SELECT 
                j.operation as operation_type,
                COUNT(*) as total_count,
                SUM(CASE WHEN j.status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN j.status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                SUM(CASE WHEN j.status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                ROUND(AVG(EXTRACT(EPOCH FROM (j.completed_at - j.created_at)) * 1000)) as avg_time_ms
            FROM jobs j
            WHERE j.completed_at IS NOT NULL
            GROUP BY j.operation
            ORDER BY total_count DESC
        """
        
        operations = db.execute_query(query)
        
        # Convert to serializable format
        operations_list = []
        for row in operations:
            operations_list.append({
                'operation': row['operation_type'],
                'count': int(row['total_count']) if row['total_count'] else 0,
                'completed_count': int(row['completed_count']) if row['completed_count'] else 0,
                'failed_count': int(row['failed_count']) if row['failed_count'] else 0,
                'pending': int(row['pending_count']) if row['pending_count'] else 0,
                'avg_time_ms': float(row['avg_time_ms']) if row['avg_time_ms'] else 0
            })
        
        # Format response
        response = {
            'operations': operations_list,
            'cached': False,
            'cache_ttl': CACHE_TTL
        }
        
        # Store in cache
        cache.set(cache_key, json.dumps(response), ttl=CACHE_TTL)
        
        return jsonify(response)


class JobsEndpoint:
    """Handles /api/jobs endpoint. This endpoint is provided as an example."""
    
    @staticmethod
    def get():
        """
        Get job queue information.
        This demonstrates using multiple queries in one endpoint.
        """
        cache_key = 'admin:jobs'
        jobs_ttl = 60  # Shorter TTL for jobs
        
        # Check cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            response = json.loads(cached_data)
            response['cached'] = True
            return jsonify(response)
        
        # Query 1: Recent jobs
        jobs_query = """
            SELECT 
                j.id,
                j.user_id,
                u.username,
                j.operation,
                j.status,
                j.created_at,
                j.completed_at
            FROM jobs j
            INNER JOIN users u ON j.user_id = u.id
            ORDER BY j.created_at DESC
            LIMIT 50
        """
        
        jobs = db.execute_query(jobs_query)
        
        # Convert to serializable format
        jobs_list = []
        for row in jobs:
            jobs_list.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'],
                'operation': row['operation'],
                'status': row['status'],
                'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                'completed_at': row['completed_at'].isoformat() if row.get('completed_at') else None
            })
        
        # Query 2: Queue statistics
        stats_query = """
            SELECT 
                status,
                COUNT(*) as count
            FROM jobs
            GROUP BY status
        """
        
        stats = db.execute_query(stats_query)
        
        # Initialize with defaults to avoid undefined in UI
        queue_stats = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0
        }
        # Update with actual values from query
        for stat in stats:
            queue_stats[stat['status']] = int(stat['count'])
        
        # Format response
        response = {
            'jobs': jobs_list,
            'queue_stats': queue_stats,
            'cached': False,
            'cache_ttl': jobs_ttl
        }
        
        # Store in cache
        cache.set(cache_key, json.dumps(response), ttl=jobs_ttl)
        
        return jsonify(response)


class HealthEndpoint:
    """Handles /health endpoint."""
    
    @staticmethod
    def get():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'database': db.connection_pool is not None,
            'cache': cache.redis_client is not None
        })
