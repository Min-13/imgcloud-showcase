# Compiler
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2

# Libraries
LIBS = -lpqxx -lpq -lhiredis

# Target
TARGET = admin

# Source files
SOURCES = main.cpp db.cpp cache.cpp endpoints.cpp http_server.cpp
HEADERS = db.h cache.h endpoints.h http_server.h

# Object files
OBJECTS = $(SOURCES:.cpp=.o)

# Default target
all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LIBS)

%.o: %.cpp $(HEADERS)
	$(CXX) $(CXXFLAGS) -c $<

clean:
	rm -f $(OBJECTS) $(TARGET)

.PHONY: all clean
