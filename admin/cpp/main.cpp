/**
 * Admin Interface C++ Application.
 * This file sets up the HTTP server and routing.
 * Students implement endpoints in endpoints.cpp.
 */

#include <cstdlib>
#include "http_server.h"

int main() {
    const char* port_env = std::getenv("ADMIN_PORT");
    int port = port_env ? std::atoi(port_env) : 8090;
    
    HTTPServer server(port);
    server.start();
    
    return 0;
}
