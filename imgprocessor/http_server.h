/**
 * HTTP Server - Simple HTTP server for health checks
 * 
 * This server only handles /health endpoint for service monitoring.
 * All image processing is done via gRPC.
 */

#ifndef HTTP_SERVER_H
#define HTTP_SERVER_H

#include <string>
#include <atomic>

class HttpServer {
public:
    /**
     * Constructor
     * @param port Port number for HTTP server
     */
    explicit HttpServer(int port);
    
    /**
     * Destructor - ensures cleanup
     */
    ~HttpServer();
    
    /**
     * Start the HTTP server (blocking call)
     */
    void start();
    
    /**
     * Stop the HTTP server
     */
    void stop();

private:
    int port_;
    int server_fd_;
    std::atomic<bool> running_;
    
    /**
     * Handle incoming HTTP request
     * @param client_socket Socket connected to the client
     */
    void handleRequest(int client_socket);
};

#endif // HTTP_SERVER_H
