#include "db.h"
#include <cstdlib>
#include <regex>
#include <stdexcept>
#include <iostream>

DatabaseConnection::DatabaseConnection() {
    initializeConnection();
}

DatabaseConnection::~DatabaseConnection() {
    // Cleanup handled by unique_ptr
}

void DatabaseConnection::initializeConnection() {
    const char* db_url = std::getenv("DATABASE_URL");
    if (!db_url) {
        std::cerr << "ERROR: DATABASE_URL environment variable not set" << std::endl;
        return;
    }
    
    try {
        // Parse DATABASE_URL (format: postgresql://user:password@host:port/database)
        std::regex url_regex(
            R"(postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+))"
        );
        
        std::smatch matches;
        std::string url_str(db_url);
        if (!std::regex_match(url_str, matches, url_regex)) {
            std::cerr << "ERROR: Invalid DATABASE_URL format" << std::endl;
            return;
        }
        
        // Extract components
        std::string username = matches[1].str();
        std::string password = matches[2].str();
        std::string host = matches[3].str();
        std::string port = matches[4].str();
        std::string database = matches[5].str();
        
        // Build connection string for libpqxx
        connection_string = "host=" + host +
                           " port=" + port +
                           " dbname=" + database +
                           " user=" + username +
                           " password=" + password;
        
        // TODO: Pre-create some connections for the pool
        // Create 3 initial connections and store them in the 'connections' vector
        // Important: Clear the connections vector first before adding new connections
        // Use pqxx::connection constructor with connection_string: pqxx::connection(connection_string)
        // Store connections using std::make_unique and connections.push_back()
        
        std::cout << "Connected to PostgreSQL with connection pool at " 
                  << host << ":" << port << "/" << database << std::endl;
                  
    } catch (const std::exception& e) {
        std::cerr << "Database initialization error: " << e.what() << std::endl;
        std::lock_guard<std::mutex> lock(pool_mutex);
        connections.clear();
    }
}

std::shared_ptr<pqxx::connection> DatabaseConnection::getConnection() {
    std::lock_guard<std::mutex> lock(pool_mutex);
    
    // If we have available connections, return one
    if (!connections.empty()) {
        auto conn = std::move(connections.back());
        connections.pop_back();
        // Return with custom deleter that returns to pool
        return std::shared_ptr<pqxx::connection>(conn.release(), 
            [this](pqxx::connection* c) { 
                this->returnConnectionToPool(std::unique_ptr<pqxx::connection>(c)); 
            });
    }
    
    // Create new connection if pool is empty (max 10)
    if (connection_string.empty()) {
        return nullptr;
    }
    
    try {
        auto conn = std::make_unique<pqxx::connection>(connection_string);
        return std::shared_ptr<pqxx::connection>(conn.release(),
            [this](pqxx::connection* c) { 
                this->returnConnectionToPool(std::unique_ptr<pqxx::connection>(c)); 
            });
    } catch (const std::exception& e) {
        std::cerr << "Failed to create connection: " << e.what() << std::endl;
        return nullptr;
    }
}

void DatabaseConnection::returnConnectionToPool(std::unique_ptr<pqxx::connection> conn) {
    if (!conn) return;
    
    std::lock_guard<std::mutex> lock(pool_mutex);
    if (connections.size() < 10) {
        connections.push_back(std::move(conn));
    }
    // Otherwise let it destruct
}

void DatabaseConnection::releaseConnection(std::shared_ptr<pqxx::connection> conn) {
    // This method is kept for interface compatibility but not used
    // The deleter in getConnection handles returning to pool
    (void)conn; // Suppress unused parameter warning
}

std::vector<std::map<std::string, std::string>> DatabaseConnection::executeQuery(
    const std::string& query,
    const std::vector<std::string>& params
) {
    std::vector<std::map<std::string, std::string>> results;
    
    try {
        // Get a connection from the pool
        auto conn = getConnection();
        if (!conn) {
            std::cerr << "ERROR: Could not get database connection" << std::endl;
            return results;
        }
        
        // Create a transaction
        pqxx::work txn(*conn);
        
        // Execute query with or without parameters
        pqxx::result r;
        if (params.empty()) {
            r = txn.exec(query);
        } else {
            // Execute parameterized query
            // Note: This example handles up to 5 parameters
            // For more, extend the if-else chain or use variadic templates
            switch (params.size()) {
                case 1:
                    r = txn.exec_params(query, params[0]);
                    break;
                case 2:
                    r = txn.exec_params(query, params[0], params[1]);
                    break;
                case 3:
                    r = txn.exec_params(query, params[0], params[1], params[2]);
                    break;
                case 4:
                    r = txn.exec_params(query, params[0], params[1], params[2], params[3]);
                    break;
                case 5:
                    r = txn.exec_params(query, params[0], params[1], params[2], params[3], params[4]);
                    break;
                default:
                    throw std::runtime_error("Too many parameters (max 5 supported). Extend executeQuery() for more.");
            }
        }
        
        // Commit the transaction
        txn.commit();
        
        // Convert results to vector of maps
        for (const auto& row : r) {
            std::map<std::string, std::string> row_map;
            for (size_t i = 0; i < row.size(); ++i) {
                std::string col_name = r.column_name(i);
                std::string col_value = row.at(static_cast<int>(i)).is_null() ? "" : row.at(static_cast<int>(i)).c_str();
                row_map[col_name] = col_value;
            }
            results.push_back(row_map);
        }
        
        // Connection 'conn' goes out of scope here and is automatically
        // returned to the pool for reuse by other requests
        
    } catch (const pqxx::sql_error& e) {
        std::cerr << "SQL error: " << e.what() << std::endl;
        std::cerr << "Query was: " << e.query() << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Database query error: " << e.what() << std::endl;
    }
    
    return results;
}

bool DatabaseConnection::isConnected() const {
    std::lock_guard<std::mutex> lock(const_cast<std::mutex&>(pool_mutex));
    return !connections.empty() || !connection_string.empty();
}
