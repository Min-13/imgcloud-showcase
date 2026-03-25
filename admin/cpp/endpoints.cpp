/**
 * LAB05 Solution - Endpoint implementations
 * Only Users and Images endpoints are in the solutions directory.
 * Operations and Jobs are provided to students in the admin/cpp/ directory.
 */

#include "endpoints.h"
#include <cstdlib>

// Get configuration from environment
static int getCacheTTL() {
    const char* ttl_env = std::getenv("CACHE_TTL");
    return ttl_env ? std::atoi(ttl_env) : 300;
}

json UsersEndpoint::handleRequest(DatabaseConnection& db, CacheConnection& cache) {
    // TODO: Implement UsersEndpoint
    //
    // Requirements:
    // 1. Check cache first with key "admin:users"
    // 2. If cache miss, query database for users with image_count and job_count
    // 3. Convert query results to json array
    // 4. Format response with "users" array, "cached" boolean, "cache_ttl" int
    // 5. Store in cache with TTL
    // 6. Return json response
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
    //       "id": "string",
    //       "username": "string",
    //       "email": "string",
    //       "created_at": "ISO datetime string",
    //       "image_count": "string",
    //       "job_count": "string"
    //     }
    //   ],
    //   "cached": boolean,
    //   "cache_ttl": int
    // }
    //
    // Hints:
    // - Study OperationsEndpoint below for the pattern
    // - Use db.executeQuery() to get vector of maps
    // - Iterate with: for (const auto& user : users)
    // - Build json with: for (const auto& [key, value] : user)
    // - Use cache.get() which returns optional<json>
    // - Use cache.set(key, json_obj, ttl)
    // - Get TTL with: getCacheTTL()
    
    return json{
        {"users", json::array()},
        {"cached", false},
        {"cache_ttl", 0}
    };
}

json ImagesEndpoint::handleRequest(DatabaseConnection& db, CacheConnection& cache) {
    // TODO: Implement ImagesEndpoint
    //
    // Requirements:
    // 1. Check cache first with key "admin:images"
    // 2. If cache miss, query database for recent images (limit 100)
    // 3. Convert query results to json array
    // 4. Format response with "images" array, "total" count, "cached" boolean, "cache_ttl" int
    // 5. Store in cache with TTL
    // 6. Return json response
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
    //       "id": "string",
    //       "user_id": "string",
    //       "username": "string",
    //       "original_filename": "string",
    //       "file_size": "string",
    //       "content_type": "string",
    //       "upload_date": "string"
    //     }
    //   ],
    //   "total": int,
    //   "cached": boolean,
    //   "cache_ttl": int
    // }
    //
    // Hints:
    // - Study OperationsEndpoint below for the caching pattern
    // - Simply copy all database fields to JSON without renaming
    // - Iterate with: for (const auto& [key, value] : img) { img_obj[key] = value; }
    
    return json{
        {"images", json::array()},
        {"total", 0},
        {"cached", false},
        {"cache_ttl", 0}
    };
}

// NOTE: OperationsEndpoint and JobsEndpoint are provided to students
// in the admin/cpp/endpoints.cpp file and are not part of the solution.


// The following endpoints are provided to students as complete examples
// They are included here so the solution can run standalone

json OperationsEndpoint::handleRequest(DatabaseConnection& db, CacheConnection& cache) {
    const std::string cache_key = "admin:operations";
    int ttl = getCacheTTL();
    
    // Check cache first
    auto cached_data = cache.get(cache_key);
    if (cached_data.has_value()) {
        json response = cached_data.value();
        response["cached"] = true;
        return response;
    }
    
    // Cache miss - query database
    std::string query = R"(
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
    )";
    
    auto result = db.executeQuery(query);
    
    json operations_list = json::array();
    for (const auto& row : result) {
        json op = {
            {"operation", row.at("operation_type")},
            {"count", row.at("total_count")},
            {"completed_count", row.at("completed_count")},
            {"failed_count", row.at("failed_count")},
            {"pending", row.at("pending_count")},
            {"avg_time_ms", row.at("avg_time_ms")}
        };
        operations_list.push_back(op);
    }
    
    // Format response
    json response = {
        {"operations", operations_list},
        {"cached", false},
        {"cache_ttl", ttl}
    };
    
    // Store in cache
    cache.set(cache_key, response, ttl);
    
    return response;
}

json JobsEndpoint::handleRequest(DatabaseConnection& db, CacheConnection& cache) {
    const std::string cache_key = "admin:jobs";
    int jobs_ttl = 60;  // Shorter TTL for jobs
    
    // Check cache first
    auto cached_data = cache.get(cache_key);
    if (cached_data.has_value()) {
        json response = cached_data.value();
        response["cached"] = true;
        return response;
    }
    
    // Query 1: Recent jobs
    std::string jobs_query = R"(
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
    )";
    
    auto jobs = db.executeQuery(jobs_query);
    
    json jobs_list = json::array();
    for (const auto& row : jobs) {
        json job;
        for (const auto& [key, value] : row) {
            job[key] = value;
        }
        jobs_list.push_back(job);
    }
    
    // Query 2: Queue statistics
    std::string stats_query = R"(
        SELECT 
            status,
            COUNT(*) as count
        FROM jobs
        GROUP BY status
    )";
    
    auto stats = db.executeQuery(stats_query);
    
    // Initialize with defaults to avoid undefined in UI
    json queue_stats = {
        {"pending", "0"},
        {"processing", "0"},
        {"completed", "0"},
        {"failed", "0"}
    };
    
    // Update with actual values from query
    for (const auto& row : stats) {
        std::string status_val;
        std::string count_val;
        for (const auto& [key, value] : row) {
            if (key == "status") status_val = value;
            else if (key == "count") count_val = value;
        }
        if (!status_val.empty()) {
            queue_stats[status_val] = count_val;
        }
    }
    
    // Format response
    json response = {
        {"jobs", jobs_list},
        {"queue_stats", queue_stats},
        {"cached", false},
        {"cache_ttl", jobs_ttl}
    };
    
    // Store in cache
    cache.set(cache_key, response, jobs_ttl);
    
    return response;
}

json HealthEndpoint::handleRequest(DatabaseConnection& db, CacheConnection& cache) {
    json response = {
        {"status", "healthy"},
        {"database", db.isConnected()},
        {"cache", cache.isConnected()}
    };
    return response;
}
