/**
 * gRPC Server - Handles image processing requests via gRPC
 * 
 * This server implements the ImageProcessor service defined in the proto file
 * and delegates actual image processing to the ImageProcessor class.
 */

#ifndef GRPC_SERVER_H
#define GRPC_SERVER_H

#include <grpcpp/grpcpp.h>
#include "image_processor.pb.h"
#include "image_processor.grpc.pb.h"
#include "image_processor.h"
#include <string>
#include <memory>

// Implementation of the ImageProcessor gRPC service
class ImageProcessorServiceImpl final : public imageprocessor::ImageProcessor::Service {
public:
    // Handle ProcessImage RPC calls
    grpc::Status ProcessImage(grpc::ServerContext* context,
                             const imageprocessor::ProcessRequest* request,
                             imageprocessor::ProcessResponse* response) override;

private:
    ImageProcessor processor;  // Image processing operations
};

// gRPC server wrapper
class GrpcServer {
public:
    /**
     * Constructor
     * @param port Port number for gRPC server
     */
    explicit GrpcServer(int port);
    
    /**
     * Start the gRPC server (blocking call)
     */
    void start();
    
    /**
     * Stop the gRPC server
     */
    void stop();

private:
    int port_;
    std::unique_ptr<grpc::Server> server_;
    ImageProcessorServiceImpl service_;
};

#endif // GRPC_SERVER_H
