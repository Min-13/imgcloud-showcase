/**
 * gRPC Server implementation
 */

#include "grpc_server.h"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <vector>

// Process image RPC handler
grpc::Status ImageProcessorServiceImpl::ProcessImage(
    grpc::ServerContext* context,
    const imageprocessor::ProcessRequest* request,
    imageprocessor::ProcessResponse* response) {
    
    try {
        // Validate image data size (max 10MB to prevent DoS)
        const std::string& image_data_str = request->image_data();
        constexpr size_t MAX_IMAGE_SIZE = 10 * 1024 * 1024;  // 10MB
        if (image_data_str.size() > MAX_IMAGE_SIZE) {
            return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT, 
                               "Image data exceeds maximum size of 10MB");
        }
        
        // Extract image data from request
        std::vector<uchar> image_buffer(image_data_str.begin(), image_data_str.end());
        
        // Decode image using OpenCV
        cv::Mat image = cv::imdecode(image_buffer, cv::IMREAD_COLOR);
        if (image.empty()) {
            return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT, "Failed to decode image");
        }
        
        // Process the image
        cv::Mat result = processor.processImage(
            image,
            request->operation(),
            request->width(),
            request->height(),
            request->kernel_size(),
            request->angle(),
            request->direction()
        );
        
        // Encode result as PNG
        std::vector<uchar> output_buffer;
        if (!cv::imencode(".png", result, output_buffer)) {
            return grpc::Status(grpc::StatusCode::INTERNAL, "Failed to encode image");
        }
        
        // Set response data
        response->set_image_data(output_buffer.data(), output_buffer.size());
        
        return grpc::Status::OK;
        
    } catch (const std::exception& e) {
        std::string error_msg = std::string("Processing error: ") + e.what();
        return grpc::Status(grpc::StatusCode::INTERNAL, error_msg);
    }
}

// GrpcServer constructor
GrpcServer::GrpcServer(int port) : port_(port) {}

// Start the gRPC server
void GrpcServer::start() {
    std::string server_address = "0.0.0.0:" + std::to_string(port_);
    
    grpc::ServerBuilder builder;
    
    // Listen on the given address without any authentication mechanism
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    
    // Register the service
    builder.RegisterService(&service_);
    
    // Build and start the server
    server_ = builder.BuildAndStart();
    
    if (!server_) {
        std::cerr << "Failed to start gRPC server on " << server_address << std::endl;
        return;
    }
    
    std::cout << "gRPC server listening on " << server_address << std::endl;
    
    // Wait for the server to shutdown (blocking call)
    server_->Wait();
}

// Stop the gRPC server
void GrpcServer::stop() {
    if (server_) {
        server_->Shutdown();
    }
}
