<?php
/**
 * LAB05 Solution - Endpoint implementations
 * Only Users and Images endpoints are in the solutions directory.
 * Operations and Jobs are provided to students in the admin/php/ directory.
 */

require_once 'db.php';
require_once 'cache.php';

// Configuration
$CACHE_TTL = intval(getenv('CACHE_TTL') ?: 300);

class UsersEndpoint {
    public static function get() {
        // TODO: Implement UsersEndpoint
        // 
        // Requirements:
        // 1. Check cache first with key 'admin:users'
        // 2. If cache miss, query database for users with image_count and job_count
        // 3. Format response with 'users' array, 'cached' boolean, 'cache_ttl' int
        // 4. Store in cache with TTL
        // 5. Return response array
        //
        // SQL Query Requirements (see LAB05-QUERIES.md):
        // - Join users with images and jobs tables
        // - Use COUNT(DISTINCT ...) for counts
        // - GROUP BY user fields
        // - ORDER BY created_at DESC
        //
        // JSON Response Format (see LAB05.md):
        // {
        //   "users": [
        //     {
        //       "id": int,
        //       "username": "string",
        //       "email": "string",
        //       "created_at": "ISO datetime",
        //       "image_count": int,
        //       "job_count": int
        //     }
        //   ],
        //   "cached": boolean,
        //   "cache_ttl": int
        // }
        //
        // Hints:
        // - Study OperationsEndpoint below for the pattern
        // - Use prepared statements (see LAB05-PHP.md)
        // - Remember to set cache TTL from global $CACHE_TTL
        
        return [
            'users' => [],
            'cached' => false,
            'cache_ttl' => 0
        ];
    }
}

class ImagesEndpoint {
    public static function get() {
        // TODO: Implement ImagesEndpoint
        //
        // Requirements:
        // 1. Check cache first with key 'admin:images'
        // 2. If cache miss, query database for recent images (limit 100)
        // 3. Format response with 'images' array, 'total' count, 'cached' boolean, 'cache_ttl' int
        // 4. Store in cache with TTL
        // 5. Return response array
        //
        // SQL Query Requirements (see LAB05-QUERIES.md):
        // - Join images with users table
        // - SELECT: id, user_id, username, original_filename, file_size, content_type, upload_date
        // - ORDER BY upload_date DESC
        // - LIMIT 100
        //
        // ⚠️ CRITICAL: Use database column names AS-IS in response (admin.html expects these exact names):
        // - original_filename (NOT "filename")
        // - file_size (NOT "size")
        // - upload_date (NOT "uploaded_at")
        //
        // JSON Response Format (see LAB05.md):
        // {
        //   "images": [
        //     {
        //       "id": int,
        //       "user_id": int,
        //       "username": "string",
        //       "original_filename": "string",
        //       "file_size": int,
        //       "content_type": "string",
        //       "upload_date": "ISO datetime"
        //     }
        //   ],
        //   "total": int,
        //   "cached": boolean,
        //   "cache_ttl": int
        // }
        //
        // Hints:
        // - Study OperationsEndpoint below for the caching pattern
        // - You must rename fields from database columns to match UI expectations
        
        return [
            'images' => [],
            'total' => 0,
            'cached' => false,
            'cache_ttl' => 0
        ];
    }
}

class OperationsEndpoint {
    /**
     * Handle GET /api/operations
     * This endpoint is provided as an example.
     * Study this implementation to understand the pattern for UsersEndpoint and ImagesEndpoint.
     */
    public static function get() {
        global $db, $cache, $CACHE_TTL;
        $cache_key = 'admin:operations';
        
        // Check cache first
        $cached_data = $cache->get($cache_key);
        if ($cached_data !== null) {
            $response = json_decode($cached_data, true);
            $response['cached'] = true;
            return $response;
        }
        
        // Cache miss - query database
        $query = "
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
        ";
        
        $operations = $db->executeQuery($query);
        
        // Convert to proper format
        $operations_list = [];
        foreach ($operations as $row) {
            $operations_list[] = [
                'operation' => $row['operation_type'],
                'count' => (int)($row['total_count'] ?? 0),
                'completed_count' => (int)($row['completed_count'] ?? 0),
                'failed_count' => (int)($row['failed_count'] ?? 0),
                'pending' => (int)($row['pending_count'] ?? 0),
                'avg_time_ms' => (float)($row['avg_time_ms'] ?? 0)
            ];
        }
        
        // Format response
        $response = [
            'operations' => $operations_list,
            'cached' => false,
            'cache_ttl' => $CACHE_TTL
        ];
        
        // Store in cache
        $cache->set($cache_key, json_encode($response), $CACHE_TTL);
        
        return $response;
    }
}

class JobsEndpoint {
    /**
     * Handle GET /api/jobs
     * This endpoint is provided as an example.
     * It demonstrates using multiple queries in one endpoint.
     */
    public static function get() {
        global $db, $cache;
        $cache_key = 'admin:jobs';
        $jobs_ttl = 60;  // Shorter TTL for jobs
        
        // Check cache first
        $cached_data = $cache->get($cache_key);
        if ($cached_data !== null) {
            $response = json_decode($cached_data, true);
            $response['cached'] = true;
            return $response;
        }
        
        // Query 1: Recent jobs
        $jobs_query = "
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
        ";
        
        $jobs = $db->executeQuery($jobs_query);
        
        // Query 2: Queue statistics
        $stats_query = "
            SELECT 
                status,
                COUNT(*) as count
            FROM jobs
            GROUP BY status
        ";
        
        $stats = $db->executeQuery($stats_query);
        
        // Initialize with defaults to avoid undefined in UI
        $queue_stats = [
            'pending' => 0,
            'processing' => 0,
            'completed' => 0,
            'failed' => 0
        ];
        // Update with actual values from query
        foreach ($stats as $stat) {
            $queue_stats[$stat['status']] = (int)$stat['count'];
        }
        
        // Format response
        $response = [
            'jobs' => $jobs,
            'queue_stats' => $queue_stats,
            'cached' => false,
            'cache_ttl' => $jobs_ttl
        ];
        
        // Store in cache
        $cache->set($cache_key, json_encode($response), $jobs_ttl);
        
        return $response;
    }
}

class HealthEndpoint {
    public static function get() {
        global $db, $cache;
        return [
            'status' => 'healthy',
            'database' => $db->isConnected(),
            'cache' => $cache->isConnected()
        ];
    }
}
?>
