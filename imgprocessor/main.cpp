/**
 * Image Processor Service - Main entry point
 * 
 * This service provides image processing capabilities via gRPC.
 * It also runs a minimal HTTP server for health checks.
 * 
 * Architecture:
 * - gRPC server (port 50051): Handles image processing requests
 * - HTTP server (port 8080): Provides /health endpoint for monitoring
 * - ImageProcessor: Core OpenCV-based image processing logic
 * 
 * The service runs both servers concurrently using separate threads.
 */

#include "grpc_server.h"
#include "http_server.h"
#include <iostream>
#include <thread>
#include <csignal>
#include <memory>
#include <atomic>

// Atomic flag for signal handling (async-signal-safe)
std::atomic<bool> g_shutdown_requested(false);

// Global pointers for graceful shutdown
std::unique_ptr<GrpcServer> g_grpc_server;
std::unique_ptr<HttpServer> g_http_server;

/**
 * Signal handler for graceful shutdown (async-signal-safe)
 */
void signalHandler(int signum) {
    // Only set atomic flag - do not call non-async-signal-safe functions
    g_shutdown_requested.store(true);
    (void)signum;  // Suppress unused parameter warning
}

int main(int argc, char* argv[]) {
    // Default ports
    int grpc_port = 50051;
    int http_port = 8080;
    
    // Parse command line arguments
    // Usage: ./imgprocessor [grpc_port] [http_port]
    if (argc > 1) {
        grpc_port = std::atoi(argv[1]);
    }
    if (argc > 2) {
        http_port = std::atoi(argv[2]);
    }
    
    // Check environment variables
    const char* env_grpc_port = std::getenv("GRPC_PORT");
    if (env_grpc_port) {
        grpc_port = std::atoi(env_grpc_port);
    }
    
    const char* env_http_port = std::getenv("HTTP_PORT");
    if (env_http_port) {
        http_port = std::atoi(env_http_port);
    }
    
    // Register signal handlers for graceful shutdown
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    
    std::cout << "Starting Image Processor Service..." << std::endl;
    std::cout << "gRPC server will listen on port " << grpc_port << std::endl;
    std::cout << "HTTP health server will listen on port " << http_port << std::endl;
    
    // Create server instances
    g_grpc_server = std::make_unique<GrpcServer>(grpc_port);
    g_http_server = std::make_unique<HttpServer>(http_port);
    
    // Start HTTP server in a separate thread
    std::thread http_thread([]() {
        g_http_server->start();
    });
    
    // Start gRPC server in the main thread (blocking)
    // This is the primary service, so it runs in the main thread
    g_grpc_server->start();
    
    // Check if shutdown was requested
    if (g_shutdown_requested.load()) {
        std::cout << "\nShutdown requested, stopping servers..." << std::endl;
        if (g_http_server) {
            g_http_server->stop();
        }
        if (g_grpc_server) {
            g_grpc_server->stop();
        }
    }
    
    // Wait for HTTP thread to complete
    if (http_thread.joinable()) {
        http_thread.join();
    }
    
    std::cout << "Service shutdown complete" << std::endl;
    return 0;
}
