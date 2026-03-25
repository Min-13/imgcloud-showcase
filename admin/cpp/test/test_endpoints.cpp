/**
 * Unit tests for endpoints module (endpoints.cpp/endpoints.h)
 * Tests all 5 endpoints: Users, Images, Operations, Jobs, Health
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "../endpoints.h"
#include "../db.h"
#include "../cache.h"

using ::testing::_;
using ::testing::Return;
using json = nlohmann::json;

class EndpointsTest : public ::testing::Test {
protected:
    void SetUp() override {
        setenv("DATABASE_URL", "postgresql://testuser:testpass@localhost:5432/testdb", 1);
        setenv("REDIS_URL", "redis://localhost:6379/0", 1);
    }
    
    void TearDown() override {
        unsetenv("DATABASE_URL");
        unsetenv("REDIS_URL");
    }
};

TEST_F(EndpointsTest, UsersEndpointExists) {
    // Test that UsersEndpoint class exists
    EXPECT_NO_THROW({
        UsersEndpoint endpoint;
    });
}

TEST_F(EndpointsTest, ImagesEndpointExists) {
    // Test that ImagesEndpoint class exists
    EXPECT_NO_THROW({
        ImagesEndpoint endpoint;
    });
}

TEST_F(EndpointsTest, OperationsEndpointExists) {
    // Test that OperationsEndpoint class exists
    EXPECT_NO_THROW({
        OperationsEndpoint endpoint;
    });
}

TEST_F(EndpointsTest, JobsEndpointExists) {
    // Test that JobsEndpoint class exists
    EXPECT_NO_THROW({
        JobsEndpoint endpoint;
    });
}

TEST_F(EndpointsTest, HealthEndpointExists) {
    // Test that HealthEndpoint class exists
    EXPECT_NO_THROW({
        HealthEndpoint endpoint;
    });
}

TEST_F(EndpointsTest, UsersEndpointReturnsJson) {
    // Test that Users endpoint returns valid JSON
    UsersEndpoint endpoint;
    
    DatabaseConnection db;
    CacheConnection cache;
    
    auto result = endpoint.handleRequest(db, cache);
    
    // Should return valid JSON string
    EXPECT_NO_THROW({
        json parsed = json::parse(result);
        EXPECT_TRUE(parsed.contains("users"));
        EXPECT_TRUE(parsed.contains("cached"));
    });
}

TEST_F(EndpointsTest, ImagesEndpointReturnsJson) {
    // Test that Images endpoint returns valid JSON
    ImagesEndpoint endpoint;
    
    DatabaseConnection db;
    CacheConnection cache;
    
    auto result = endpoint.handleRequest(db, cache);
    
    EXPECT_NO_THROW({
        json parsed = json::parse(result);
        EXPECT_TRUE(parsed.contains("images"));
        EXPECT_TRUE(parsed.contains("cached"));
    });
}

TEST_F(EndpointsTest, OperationsEndpointStructure) {
    // Test Operations endpoint response structure
    OperationsEndpoint endpoint;
    
    DatabaseConnection db;
    CacheConnection cache;
    
    auto result = endpoint.handleRequest(db, cache);
    
    EXPECT_NO_THROW({
        json parsed = json::parse(result);
        EXPECT_TRUE(parsed.contains("operations"));
        EXPECT_TRUE(parsed.contains("cached"));
        EXPECT_TRUE(parsed.contains("cache_ttl"));
        
        if (!parsed["operations"].empty()) {
            auto op = parsed["operations"][0];
            EXPECT_TRUE(op.contains("operation"));
            EXPECT_TRUE(op.contains("total"));
            EXPECT_TRUE(op.contains("avg_time_ms"));
        }
    });
}

TEST_F(EndpointsTest, JobsEndpointStructure) {
    // Test Jobs endpoint response structure
    JobsEndpoint endpoint;
    
    DatabaseConnection db;
    CacheConnection cache;
    
    auto result = endpoint.handleRequest(db, cache);
    
    EXPECT_NO_THROW({
        json parsed = json::parse(result);
        EXPECT_TRUE(parsed.contains("jobs"));
        EXPECT_TRUE(parsed.contains("queue_stats"));
        EXPECT_TRUE(parsed.contains("cached"));
        
        auto stats = parsed["queue_stats"];
        EXPECT_TRUE(stats.contains("pending"));
        EXPECT_TRUE(stats.contains("processing"));
        EXPECT_TRUE(stats.contains("completed"));
        EXPECT_TRUE(stats.contains("failed"));
    });
}

TEST_F(EndpointsTest, HealthEndpointStructure) {
    // Test Health endpoint response structure
    HealthEndpoint endpoint;
    
    DatabaseConnection db;
    CacheConnection cache;
    
    auto result = endpoint.handleRequest(db, cache);
    
    EXPECT_NO_THROW({
        json parsed = json::parse(result);
        EXPECT_TRUE(parsed.contains("status"));
        EXPECT_TRUE(parsed.contains("database"));
        EXPECT_TRUE(parsed.contains("cache"));
        
        // Status should be "healthy" or "unhealthy"
        std::string status = parsed["status"];
        EXPECT_TRUE(status == "healthy" || status == "unhealthy");
    });
}

TEST_F(EndpointsTest, EndpointsImplementCaching) {
    // Test that endpoints use caching
    UsersEndpoint endpoint;
    
    DatabaseConnection db;
    CacheConnection cache;
    
    // First call - cache miss
    auto result1 = endpoint.handleRequest(db, cache);
    json parsed1 = json::parse(result1);
    
    // Should have cached flag
    EXPECT_TRUE(parsed1.contains("cached"));
    EXPECT_TRUE(parsed1.contains("cache_ttl"));
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
