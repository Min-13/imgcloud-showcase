# Makefile for Image Processor with gRPC

CXX = g++
CXXFLAGS = -std=c++14 -Wall -O2 -pthread
OPENCV_FLAGS = $(shell pkg-config --cflags --libs opencv4 2>/dev/null || pkg-config --cflags --libs opencv)
GRPC_FLAGS = $(shell pkg-config --cflags --libs grpc++ grpc protobuf)

# Proto compiler
PROTOC = protoc
GRPC_CPP_PLUGIN = grpc_cpp_plugin
GRPC_CPP_PLUGIN_PATH ?= $(shell which $(GRPC_CPP_PLUGIN))

# Target binary
TARGET = imgprocessor

# Source files
SOURCES = main.cpp \
          image_processor.cpp \
          grpc_server.cpp \
          http_server.cpp

# Proto files
PROTO_SRC = image_processor.proto
PROTO_GEN = image_processor.pb.cc image_processor.grpc.pb.cc
PROTO_HDR = image_processor.pb.h image_processor.grpc.pb.h

# Object files
OBJECTS = $(SOURCES:.cpp=.o) $(PROTO_GEN:.cc=.o)

all: $(TARGET)

# Generate both proto files in a single rule to avoid parallel build issues
image_processor.pb.cc image_processor.pb.h image_processor.grpc.pb.cc image_processor.grpc.pb.h: image_processor.proto
	$(PROTOC) --cpp_out=. --grpc_out=. --plugin=protoc-gen-grpc=$(GRPC_CPP_PLUGIN_PATH) $<

# Compile source files
%.o: %.cpp $(PROTO_HDR)
	$(CXX) $(CXXFLAGS) $(OPENCV_FLAGS) $(GRPC_FLAGS) -c $< -o $@

# Compile proto files
%.o: %.cc
	$(CXX) $(CXXFLAGS) $(GRPC_FLAGS) -c $< -o $@

# Link target
$(TARGET): $(PROTO_GEN) $(OBJECTS)
	$(CXX) $(CXXFLAGS) $(OBJECTS) -o $(TARGET) $(OPENCV_FLAGS) $(GRPC_FLAGS)

clean:
	rm -f $(TARGET) $(OBJECTS) $(PROTO_GEN) $(PROTO_HDR)

.PHONY: all clean
