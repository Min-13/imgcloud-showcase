# LAB03 - Communication Between Services

This document explains how the frontend and processor services communicate using gRPC and Protocol Buffers.

## Communication Protocols

The frontend and processor communicate via **gRPC** for image processing operations, with HTTP maintained only for health checks.

## Protocol Buffers Definition

The service contract is defined in `imgprocessor/image_processor.proto`:

```protobuf
syntax = "proto3";

service ImageProcessor {
  rpc ProcessImage(ProcessRequest) returns (ProcessResponse);
}

message ProcessRequest {
  bytes image_data = 1;
  string operation = 2;
  int32 width = 3;
  int32 height = 4;
  int32 kernel_size = 5;
  int32 angle = 6;
  string direction = 7;
}

message ProcessResponse {
  bytes image_data = 1;
  string error = 2;
}
```

This proto file defines:
- **ProcessRequest**: Contains the image bytes, operation name, and all possible parameters
- **ProcessResponse**: Returns the processed image bytes or an error message
- **ProcessImage RPC**: The remote procedure call for image processing

## Using the Proto File in Your Frontend

The proto file is located in `imgprocessor/image_processor.proto`. To use it in your frontend service:

1. **Copy the proto file** to your frontend directory during the Docker build
2. **Compile it to Python code** using the Protocol Buffers compiler
3. **Import the generated modules** in your Python application

### Compiling Proto Files to Python

During your Docker build, you need to compile the proto file using `grpc_tools.protoc`:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. image_processor.proto
```

This command:
- `-I.` specifies the include directory (current directory)
- `--python_out=.` generates Python message classes (`image_processor_pb2.py`)
- `--grpc_python_out=.` generates Python gRPC client/server code (`image_processor_pb2_grpc.py`)
- `image_processor.proto` is the input proto file

**Why compile during Docker build?**
- Ensures the generated code matches the proto file version
- Avoids committing generated code to your repository
- Makes the build reproducible and self-contained
- Each service generates code in its own language (Python for frontend, C++ for processor)

## Environment Variables

The frontend uses these environment variables to locate the processor:

- `PROCESSOR_HOST`: Hostname or IP of the processor service (default: "localhost", in Docker: "imgprocessor")
- `PROCESSOR_GRPC_PORT`: Port number for gRPC communication (default: "50051")
- `PROCESSOR_HTTP_PORT`: Port number for HTTP health checks (default: "8080")

## Example Communication Flow

1. User uploads image via web UI at `http://csc.wils.one:30090` (your assigned public port)
2. Frontend receives POST request at `/process` endpoint
3. Frontend creates a gRPC client and connects to `STUDENTNAME-imgprocessor:50051` (internal Docker network)
4. Frontend sends `ProcessRequest` with image bytes, operation, and parameters over gRPC
5. Processor receives the request, performs the operation using OpenCV
6. Processor returns `ProcessResponse` with processed image bytes over gRPC
7. Frontend sends processed image back to user's browser

**Note**: Health checks still use HTTP for simplicity:
- Frontend health: `http://csc.wils.one:30090/health` (publicly accessible)
- Processor health: `http://STUDENTNAME-imgprocessor:8080/health` (internal Docker network only, accessible from frontend)
