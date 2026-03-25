/**
 * Database connection module for admin interface - Solution
 * This version implements a manual connection pool.
 */

#ifndef DB_H
#define DB_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <mutex>
#include <pqxx/pqxx>

class DatabaseConnection {
public:
    DatabaseConnection();
    ~DatabaseConnection();
    
    /**
     * Execute a SQL query and return results.
     * 
     * @param query SQL query with placeholders ($1, $2, etc.)
     * @param params Vector of parameters to bind
     * @return Vector of maps representing query results
     */
    std::vector<std::map<std::string, std::string>> executeQuery(
        const std::string& query,
        const std::vector<std::string>& params = {}
    );
    
    bool isConnected() const;

private:
    void initializeConnection();
    std::shared_ptr<pqxx::connection> getConnection();
    void releaseConnection(std::shared_ptr<pqxx::connection> conn);
    void returnConnectionToPool(std::unique_ptr<pqxx::connection> conn);
    
    // Manual connection pool
    std::vector<std::unique_ptr<pqxx::connection>> connections;
    std::mutex pool_mutex;
    std::string connection_string;
};

#endif // DB_H
