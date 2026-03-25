/**
 * HTTP Server implementation.
 * This file is provided to students - no modifications needed.
 */

#include "http_server.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

using json = nlohmann::json;

HTTPServer::HTTPServer(int port) : port(port), server_socket(-1) {
    // Initialize database and cache connections
    db = std::make_unique<DatabaseConnection>();
    cache = std::make_unique<CacheConnection>();
    
    // Register endpoints
    registerEndpoints();
}

HTTPServer::~HTTPServer() {
    if (server_socket >= 0) {
        close(server_socket);
    }
}

void HTTPServer::registerEndpoints() {
    endpoints.push_back(std::make_unique<UsersEndpoint>());
    endpoints.push_back(std::make_unique<ImagesEndpoint>());
    endpoints.push_back(std::make_unique<OperationsEndpoint>());
    endpoints.push_back(std::make_unique<JobsEndpoint>());
    endpoints.push_back(std::make_unique<HealthEndpoint>());
}

bool HTTPServer::createSocket() {
    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket < 0) {
        std::cerr << "ERROR: Cannot create socket" << std::endl;
        return false;
    }
    
    int opt = 1;
    setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);
    
    if (bind(server_socket, (struct sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "ERROR: Cannot bind to port " << port << std::endl;
        close(server_socket);
        server_socket = -1;
        return false;
    }
    
    if (listen(server_socket, 10) < 0) {
        std::cerr << "ERROR: Cannot listen on socket" << std::endl;
        close(server_socket);
        server_socket = -1;
        return false;
    }
    
    return true;
}

void HTTPServer::start() {
    if (!createSocket()) {
        return;
    }
    
    std::cout << "Starting admin interface on port " << port << std::endl;
    
    // Accept connections
    while (true) {
        int client_socket = accept(server_socket, nullptr, nullptr);
        if (client_socket < 0) {
            std::cerr << "ERROR: Cannot accept connection" << std::endl;
            continue;
        }
        
        handleClient(client_socket);
        close(client_socket);
    }
}

void HTTPServer::handleClient(int client_socket) {
    char buffer[4096] = {0};
    ssize_t bytes_read = read(client_socket, buffer, sizeof(buffer) - 1);
    if (bytes_read <= 0) {
        return;
    }
    
    std::string request(buffer, bytes_read);
    std::istringstream request_stream(request);
    std::string method, path, version;
    request_stream >> method >> path >> version;
    
    if (path == "/" || path == "/index.html") {
        serveStaticFile(client_socket);
    } else {
        handleAPIRequest(client_socket, path);
    }
}

void HTTPServer::serveStaticFile(int client_socket) {
    std::string file_path = "static/admin.html";
    std::ifstream file(file_path);
    if (!file.is_open()) {
        sendResponse(client_socket, 404, "Not Found", "text/plain", "File not found");
        return;
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    sendResponse(client_socket, 200, "OK", "text/html", buffer.str());
}

void HTTPServer::handleAPIRequest(int client_socket, const std::string& path) {
    // Find matching endpoint
    for (const auto& endpoint : endpoints) {
        if (endpoint->getPath() == path) {
            json response = endpoint->handleRequest(*db, *cache);
            sendResponse(client_socket, 200, "OK", "application/json", response.dump());
            return;
        }
    }
    
    // No matching endpoint
    sendResponse(client_socket, 404, "Not Found", "text/plain", "Not Found");
}

void HTTPServer::sendResponse(int client_socket, int status_code, const std::string& status_text,
                 const std::string& content_type, const std::string& body) {
    std::ostringstream response;
    response << "HTTP/1.1 " << status_code << " " << status_text << "\r\n";
    response << "Content-Type: " << content_type << "\r\n";
    response << "Content-Length: " << body.length() << "\r\n";
    response << "Connection: close\r\n";
    response << "\r\n";
    response << body;
    
    std::string resp_str = response.str();
    send(client_socket, resp_str.c_str(), resp_str.length(), 0);
}
