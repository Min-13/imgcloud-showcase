/**
 * HTTP Server implementation
 * Minimal HTTP server for health check endpoint only
 */

#include "http_server.h"
#include <iostream>
#include <sstream>
#include <cstring>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>

HttpServer::HttpServer(int port) 
    : port_(port), server_fd_(-1), running_(false) {}

HttpServer::~HttpServer() {
    stop();
}

void HttpServer::handleRequest(int client_socket) {
    char buffer[4096];
    
    // Read request
    int bytes_read = read(client_socket, buffer, sizeof(buffer) - 1);
    if (bytes_read <= 0) {
        close(client_socket);
        return;
    }
    
    buffer[bytes_read] = '\0';
    std::string request(buffer);
    
    // Parse request line
    std::istringstream iss(request);
    std::string method, path, version;
    iss >> method >> path >> version;
    
    // Handle health check endpoint
    if (path == "/health" && method == "GET") {
        std::string body = "{\"status\":\"healthy\",\"message\":\"Service is running\"}";
        std::ostringstream response;
        response << "HTTP/1.1 200 OK\r\n"
                << "Content-Type: application/json\r\n"
                << "Content-Length: " << body.length() << "\r\n"
                << "Access-Control-Allow-Origin: *\r\n"
                << "\r\n"
                << body;
        
        std::string response_str = response.str();
        ssize_t written = write(client_socket, response_str.c_str(), response_str.length());
        (void)written;  // Suppress unused variable warning
        close(client_socket);
        return;
    }
    
    // Handle OPTIONS for CORS preflight
    if (method == "OPTIONS") {
        std::string response = "HTTP/1.1 200 OK\r\n"
                             "Access-Control-Allow-Origin: *\r\n"
                             "Access-Control-Allow-Methods: GET, OPTIONS\r\n"
                             "Access-Control-Allow-Headers: Content-Type\r\n"
                             "Content-Length: 0\r\n"
                             "\r\n";
        ssize_t written = write(client_socket, response.c_str(), response.length());
        (void)written;  // Suppress unused variable warning
        close(client_socket);
        return;
    }
    
    // 404 for all other paths
    std::string body = "{\"error\":\"Not found. Use gRPC for processing\"}";
    std::ostringstream response_stream;
    response_stream << "HTTP/1.1 404 Not Found\r\n"
                   << "Content-Type: application/json\r\n"
                   << "Content-Length: " << body.length() << "\r\n"
                   << "\r\n"
                   << body;
    std::string response = response_stream.str();
    ssize_t written = write(client_socket, response.c_str(), response.length());
    (void)written;  // Suppress unused variable warning
    close(client_socket);
}

void HttpServer::start() {
    struct sockaddr_in address;
    int opt = 1;
    
    // Create socket
    server_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd_ == 0) {
        std::cerr << "Failed to create HTTP socket" << std::endl;
        return;
    }
    
    // Set socket options to reuse address
    if (setsockopt(server_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        std::cerr << "Failed to set socket options" << std::endl;
        close(server_fd_);
        return;
    }
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port_);
    
    // Bind socket to port
    if (bind(server_fd_, (struct sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "Failed to bind HTTP server on port " << port_ << std::endl;
        close(server_fd_);
        return;
    }
    
    // Listen for connections
    if (listen(server_fd_, 10) < 0) {
        std::cerr << "Failed to listen on HTTP server" << std::endl;
        close(server_fd_);
        return;
    }
    
    running_ = true;
    std::cout << "HTTP health server listening on port " << port_ << std::endl;
    
    // Accept and handle connections
    while (running_) {
        struct sockaddr_in client_address;
        socklen_t client_len = sizeof(client_address);
        
        int client_socket = accept(server_fd_, (struct sockaddr*)&client_address, &client_len);
        if (client_socket < 0) {
            // Only log error if we're still supposed to be running
            if (running_) {
                std::cerr << "Failed to accept connection" << std::endl;
            }
            continue;
        }
        
        handleRequest(client_socket);
    }
    
    close(server_fd_);
}

void HttpServer::stop() {
    running_ = false;
    if (server_fd_ >= 0) {
        close(server_fd_);
        server_fd_ = -1;
    }
}
