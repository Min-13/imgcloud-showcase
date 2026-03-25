#include "cache.h"
#include <hiredis/hiredis.h>
#include <iostream>
#include <cstdlib>
#include <regex>

CacheConnection::CacheConnection() : redis_ctx(nullptr), port(6379), db(0) {
    initializeConnection();
}

CacheConnection::~CacheConnection() {
    if (redis_ctx) {
        redisFree(redis_ctx);
    }
}

void CacheConnection::initializeConnection() {
    const char* redis_url = std::getenv("REDIS_URL");
    if (!redis_url) {
        std::cerr << "ERROR: REDIS_URL environment variable not set" << std::endl;
        return;
    }
    
    try {
        // Parse REDIS_URL (format: redis://host:port/db or redis://host:port)
        std::regex url_regex(
            R"(redis://([^:]+)(?::(\d+))?(?:/(\d+))?)"
        );
        
        std::smatch matches;
        std::string url_str(redis_url);
        if (!std::regex_match(url_str, matches, url_regex)) {
            std::cerr << "ERROR: Invalid REDIS_URL format" << std::endl;
            return;
        }
        
        // Extract components
        host = matches[1].str();
        if (matches[2].matched) {
            port = std::stoi(matches[2].str());
        }
        if (matches[3].matched) {
            db = std::stoi(matches[3].str());
        }
        
        // Connect to Redis
        redis_ctx = redisConnect(host.c_str(), port);
        
        if (!redis_ctx || redis_ctx->err) {
            if (redis_ctx) {
                std::cerr << "Redis connection error: " << redis_ctx->errstr << std::endl;
                redisFree(redis_ctx);
                redis_ctx = nullptr;
            } else {
                std::cerr << "Redis connection error: can't allocate context" << std::endl;
            }
            return;
        }
        
        // TODO: Select database if not default
        // If the database number (db) is not 0, you need to select it
        // Redis command: SELECT <database_number>
        // Remember to free the reply after executing the command
        
        // Test connection
        redisReply* ping_reply = (redisReply*)redisCommand(redis_ctx, "PING");
        if (ping_reply && ping_reply->type == REDIS_REPLY_STATUS) {
            std::cout << "Connected to Redis at " << host << ":" << port << "/" << db << std::endl;
            freeReplyObject(ping_reply);
        } else {
            std::cerr << "ERROR: Redis PING failed" << std::endl;
            if (ping_reply) freeReplyObject(ping_reply);
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Redis initialization error: " << e.what() << std::endl;
        if (redis_ctx) {
            redisFree(redis_ctx);
            redis_ctx = nullptr;
        }
    }
}

std::optional<json> CacheConnection::get(const std::string& key) {
    if (!redis_ctx) {
        return std::nullopt;
    }
    
    try {
        redisReply* reply = (redisReply*)redisCommand(redis_ctx, "GET %s", key.c_str());
        
        if (!reply) {
            std::cerr << "ERROR: Redis GET command failed" << std::endl;
            return std::nullopt;
        }
        
        if (reply->type == REDIS_REPLY_NIL) {
            // Cache miss
            freeReplyObject(reply);
            return std::nullopt;
        }
        
        if (reply->type == REDIS_REPLY_STRING) {
            // Cache hit - parse JSON
            std::string value(reply->str, reply->len);
            freeReplyObject(reply);
            
            try {
                return json::parse(value);
            } catch (const json::parse_error& e) {
                std::cerr << "JSON parse error: " << e.what() << std::endl;
                return std::nullopt;
            }
        }
        
        freeReplyObject(reply);
        
    } catch (const std::exception& e) {
        std::cerr << "Cache get error: " << e.what() << std::endl;
    }
    
    return std::nullopt;
}

bool CacheConnection::set(const std::string& key, const json& value, int ttl) {
    if (!redis_ctx) {
        return false;
    }
    
    try {
        // Convert JSON to string
        std::string json_value = value.dump();
        
        // Execute SETEX command (SET with EXpiration)
        redisReply* reply = (redisReply*)redisCommand(
            redis_ctx,
            "SETEX %s %d %s",
            key.c_str(),
            ttl,
            json_value.c_str()
        );
        
        if (!reply) {
            std::cerr << "ERROR: Redis SETEX command failed" << std::endl;
            return false;
        }
        
        bool success = (reply->type == REDIS_REPLY_STATUS);
        freeReplyObject(reply);
        
        return success;
        
    } catch (const std::exception& e) {
        std::cerr << "Cache set error: " << e.what() << std::endl;
        return false;
    }
}

bool CacheConnection::del(const std::string& key) {
    if (!redis_ctx) {
        return false;
    }
    
    try {
        redisReply* reply = (redisReply*)redisCommand(redis_ctx, "DEL %s", key.c_str());
        
        if (!reply) {
            std::cerr << "ERROR: Redis DEL command failed" << std::endl;
            return false;
        }
        
        bool success = (reply->type == REDIS_REPLY_INTEGER);
        freeReplyObject(reply);
        
        return success;
        
    } catch (const std::exception& e) {
        std::cerr << "Cache delete error: " << e.what() << std::endl;
        return false;
    }
}

bool CacheConnection::isConnected() const {
    return redis_ctx != nullptr;
}
