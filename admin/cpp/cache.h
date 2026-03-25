/**
 * Redis cache module for admin interface.
 * Students: Complete this module to implement caching functionality.
 */

#ifndef CACHE_H
#define CACHE_H

#include <string>
#include <optional>
#include <nlohmann/json.hpp>

// Forward declaration
struct redisContext;

using json = nlohmann::json;

class CacheConnection {
public:
    CacheConnection();
    ~CacheConnection();
    
    /**
     * Get value from cache.
     */
    std::optional<json> get(const std::string& key);
    
    /**
     * Set value in cache with TTL.
     */
    bool set(const std::string& key, const json& value, int ttl = 300);
    
    /**
     * Delete value from cache.
     */
    bool del(const std::string& key);
    
    bool isConnected() const;

private:
    void initializeConnection();
    
    redisContext* redis_ctx;
    std::string host;
    int port;
    int db;
};

#endif // CACHE_H
