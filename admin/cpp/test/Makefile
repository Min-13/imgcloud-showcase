# Makefile for C++ admin tests
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -I.. -I/usr/include/postgresql
LDFLAGS = -lgtest -lgtest_main -lpqxx -lpq -lhiredis -pthread

# Test targets
TESTS = test_db test_cache test_endpoints

# Object files from parent directory
PARENT_OBJS = ../db.o ../cache.o ../endpoints.o

all: $(TESTS)

test_db: test_db.cpp $(PARENT_OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $< $(PARENT_OBJS) $(LDFLAGS)

test_cache: test_cache.cpp $(PARENT_OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $< $(PARENT_OBJS) $(LDFLAGS)

test_endpoints: test_endpoints.cpp $(PARENT_OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $< $(PARENT_OBJS) $(LDFLAGS)

# Build parent objects if needed
../db.o: ../db.cpp ../db.h
	$(MAKE) -C .. db.o

../cache.o: ../cache.cpp ../cache.h
	$(MAKE) -C .. cache.o

../endpoints.o: ../endpoints.cpp ../endpoints.h
	$(MAKE) -C .. endpoints.o

# Run all tests
test: all
	@echo "Running database tests..."
	./test_db
	@echo "\nRunning cache tests..."
	./test_cache
	@echo "\nRunning endpoints tests..."
	./test_endpoints

clean:
	rm -f $(TESTS) *.o

.PHONY: all test clean
