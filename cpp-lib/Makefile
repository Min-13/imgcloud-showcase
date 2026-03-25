# Makefile for imgutils C++ library

CXX = g++
CXXFLAGS = -Wall -fPIC -O2
AR = ar
ARFLAGS = rcs

# Library name
LIB_NAME = libimgutils
STATIC_LIB = $(LIB_NAME).a
SHARED_LIB = $(LIB_NAME).so

# Source files
SOURCES = imgutils.cpp
OBJECTS = $(SOURCES:.cpp=.o)
HEADERS = imgutils.h

# Default target
all: static shared

# Build static library
static: $(STATIC_LIB)

$(STATIC_LIB): $(OBJECTS)
	$(AR) $(ARFLAGS) $@ $^

# Build shared library
shared: $(SHARED_LIB)

$(SHARED_LIB): $(OBJECTS)
	$(CXX) -shared -o $@ $^

# Compile object files
%.o: %.cpp $(HEADERS)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	rm -f $(OBJECTS) $(STATIC_LIB) $(SHARED_LIB)

# Install libraries and headers (optional)
install: all
	mkdir -p /usr/local/lib
	mkdir -p /usr/local/include
	cp $(STATIC_LIB) $(SHARED_LIB) /usr/local/lib/
	cp $(HEADERS) /usr/local/include/
	ldconfig

.PHONY: all static shared clean install
