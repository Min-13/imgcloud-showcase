/**
 * Endpoint implementations for admin interface.
 * Students: Complete this module to implement the REST endpoints.
 */

#ifndef ENDPOINTS_H
#define ENDPOINTS_H

#include <string>
#include <nlohmann/json.hpp>
#include "db.h"
#include "cache.h"

using json = nlohmann::json;

/**
 * Base class for all endpoints.
 */
class Endpoint {
public:
    virtual ~Endpoint() = default;
    virtual json handleRequest(DatabaseConnection& db, CacheConnection& cache) = 0;
    virtual std::string getPath() const = 0;
};

/**
 * Handles /api/users endpoint.
 */
class UsersEndpoint : public Endpoint {
public:
    std::string getPath() const override { return "/api/users"; }
    json handleRequest(DatabaseConnection& db, CacheConnection& cache) override;
};

/**
 * Handles /api/images endpoint.
 */
class ImagesEndpoint : public Endpoint {
public:
    std::string getPath() const override { return "/api/images"; }
    json handleRequest(DatabaseConnection& db, CacheConnection& cache) override;
};

/**
 * Handles /api/operations endpoint.
 */
class OperationsEndpoint : public Endpoint {
public:
    std::string getPath() const override { return "/api/operations"; }
    json handleRequest(DatabaseConnection& db, CacheConnection& cache) override;
};

/**
 * Handles /api/jobs endpoint.
 */
class JobsEndpoint : public Endpoint {
public:
    std::string getPath() const override { return "/api/jobs"; }
    json handleRequest(DatabaseConnection& db, CacheConnection& cache) override;
};

/**
 * Handles /health endpoint.
 */
class HealthEndpoint : public Endpoint {
public:
    std::string getPath() const override { return "/health"; }
    json handleRequest(DatabaseConnection& db, CacheConnection& cache) override;
};

#endif // ENDPOINTS_H
