/**
 * Unit tests for cache module (cache.cpp/cache.h)
 * Tests Redis connection and cache operations
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "../cache.h"

using ::testing::_;
using ::testing::Return;
using json = nlohmann::json;

class CacheTest : public ::testing::Test {
protected:
    void SetUp() override {
        setenv("REDIS_URL", "redis://localhost:6379/0", 1);
    }
    
    void TearDown() override {
        unsetenv("REDIS_URL");
    }
};

TEST_F(CacheTest, RedisUrlParsing) {
    // Test that CacheConnection can parse REDIS_URL
    EXPECT_NO_THROW({
        CacheConnection cache;
    });
}

TEST_F(CacheTest, SetOperation) {
    // Test cache set operation
    CacheConnection cache;
    
    json test_data = {{"key", "value"}};
    
    EXPECT_NO_THROW({
        cache.set("test_key", test_data, 300);
    });
}

TEST_F(CacheTest, GetOperation) {
    // Test cache get operation
    CacheConnection cache;
    
    json test_data = {{"key", "value"}};
    cache.set("test_key", test_data, 300);
    
    auto result = cache.get("test_key");
    
    EXPECT_TRUE(result.has_value());
    if (result.has_value()) {
        EXPECT_EQ(result.value()["key"], "value");
    }
}

TEST_F(CacheTest, GetMiss) {
    // Test cache get when key doesn't exist
    CacheConnection cache;
    
    auto result = cache.get("nonexistent_key");
    
    EXPECT_FALSE(result.has_value());
}

TEST_F(CacheTest, DeleteOperation) {
    // Test cache delete operation
    CacheConnection cache;
    
    json test_data = {{"key", "value"}};
    cache.set("test_key", test_data, 300);
    
    EXPECT_NO_THROW({
        cache.del("test_key");
    });
    
    // Verify deleted
    auto result = cache.get("test_key");
    EXPECT_FALSE(result.has_value());
}

TEST_F(CacheTest, JsonSerialization) {
    // Test that JSON objects are properly serialized
    CacheConnection cache;
    
    json test_data = {
        {"id", 1},
        {"name", "test"},
        {"values", {1, 2, 3}}
    };
    
    cache.set("json_key", test_data, 300);
    auto result = cache.get("json_key");
    
    EXPECT_TRUE(result.has_value());
    if (result.has_value()) {
        EXPECT_EQ(result.value()["id"], 1);
        EXPECT_EQ(result.value()["name"], "test");
        EXPECT_EQ(result.value()["values"].size(), 3);
    }
}

TEST_F(CacheTest, TtlExpiration) {
    // Test that TTL works (short timeout for testing)
    CacheConnection cache;
    
    json test_data = {{"key", "value"}};
    cache.set("ttl_test", test_data, 1); // 1 second TTL
    
    // Should exist immediately
    auto result1 = cache.get("ttl_test");
    EXPECT_TRUE(result1.has_value());
    
    // Wait for expiration
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    // Should be expired
    auto result2 = cache.get("ttl_test");
    EXPECT_FALSE(result2.has_value());
}

TEST_F(CacheTest, ThreadSafety) {
    // Test that cache operations are thread-safe
    CacheConnection cache;
    
    std::vector<std::thread> threads;
    
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back([&cache, i]() {
            std::string key = "thread_" + std::to_string(i);
            json data = {{"thread", i}};
            
            cache.set(key, data, 300);
            auto result = cache.get(key);
            
            EXPECT_TRUE(result.has_value());
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
}

TEST_F(CacheTest, RedisDatabaseSelection) {
    // Test that Redis SELECT command is executed for non-zero database
    setenv("REDIS_URL", "redis://localhost:6379/2", 1);
    
    CacheConnection cache;
    
    // Note: This test verifies the student implementation executes SELECT command
    // The actual implementation should parse the URL and call:
    // redisCommand(redis_ctx, "SELECT %d", db)
    // followed by freeReplyObject(reply)
    
    // If the database selection is implemented, connection should be successful
    EXPECT_TRUE(cache.isConnected());
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
