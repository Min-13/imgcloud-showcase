/**
 * HTTP Server for admin interface.
 * This file is provided to students - no modifications needed.
 */

#ifndef HTTP_SERVER_H
#define HTTP_SERVER_H

#include <memory>
#include <vector>
#include "db.h"
#include "cache.h"
#include "endpoints.h"

/**
 * HTTP Server that manages endpoints and connections.
 */
class HTTPServer {
public:
    HTTPServer(int port);
    ~HTTPServer();
    
    void start();

private:
    int port;
    int server_socket;
    std::unique_ptr<DatabaseConnection> db;
    std::unique_ptr<CacheConnection> cache;
    std::vector<std::unique_ptr<Endpoint>> endpoints;
    
    void registerEndpoints();
    bool createSocket();
    void handleClient(int client_socket);
    void serveStaticFile(int client_socket);
    void handleAPIRequest(int client_socket, const std::string& path);
    void sendResponse(int client_socket, int status_code, const std::string& status_text,
                     const std::string& content_type, const std::string& body);
};

#endif // HTTP_SERVER_H
