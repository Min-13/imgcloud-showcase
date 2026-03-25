# LAB02: Multi-Stage Docker Build with Shared C++ Library

## Overview

This lab demonstrates a true multi-stage Docker build by creating a shared C++ library that is used by both the Go and Python image processing services. This approach ensures that:

1. The C++ library must be built in a builder stage
2. Both Go and Python applications depend on this library
3. The compiled library and binaries are copied to a smaller runtime stage
4. Build tools are not included in the final image, reducing its size

## The C++ Library: imgutils

The `imgutils` library is a simple C++ library located in the `cpp-lib/` directory that provides image utility functions:

### Functions

- **`calculate_pixel_count(width, height)`**: Calculates the total number of pixels in an image
- **`calculate_aspect_ratio(width, height)`**: Calculates the aspect ratio (width/height) as a floating-point number
- **`validate_dimensions(width, height)`**: Validates that both width and height are positive integers

### Files

- `imgutils.h` - C header file with function declarations (compatible with C and C++)
- `imgutils.cpp` - C++ implementation of the utility functions
- `Makefile` - Build script for creating static and shared libraries

## Building the C++ Library

The library can be built using the provided Makefile:

```bash
cd cpp-lib
make all
```

This creates:
- `libimgutils.a` - Static library (for linking at compile time)
- `libimgutils.so` - Shared library (for dynamic linking at runtime)

### Understanding Shared Libraries (.so files)

A **shared library** (`.so` on Linux, `.dylib` on macOS, `.dll` on Windows) is a compiled library that is loaded at runtime rather than being linked directly into the executable at compile time.

**Key Concepts:**

1. **Dynamic Linking**: The application loads the shared library when it starts, not when it's compiled
2. **Shared Memory**: Multiple programs can use the same library in memory, saving space
3. **Runtime Location**: The system must be able to find the `.so` file when the program runs

**How the System Finds Shared Libraries:**

The dynamic linker searches for `.so` files in this order:
1. Directories in the `LD_LIBRARY_PATH` environment variable
2. Directories specified in `/etc/ld.so.conf`
3. Default system directories like `/lib`, `/usr/lib`, `/usr/local/lib`

**For Development:**
```bash
# Temporary - only for current session
export LD_LIBRARY_PATH=/path/to/library:$LD_LIBRARY_PATH
```

**For Production:**
```bash
# Permanent - makes library system-wide
sudo cp libimgutils.so /usr/local/lib/
sudo ldconfig  # Update the system library cache
```

To clean build artifacts:
```bash
make clean
```

## Using the Library in Go

The Go application uses CGO (C bindings for Go) to call the C++ library functions.

### Integration

The file `go-example/imgutils.go` provides Go wrappers around the C library:

```go
// #cgo CFLAGS: -I../cpp-lib
// #cgo LDFLAGS: -L../cpp-lib -limgutils
// #include "imgutils.h"
import "C"

func CalculatePixelCount(width, height int) int64 {
    return int64(C.calculate_pixel_count(C.int(width), C.int(height)))
}
```

### Usage in Code

The Go service uses the library in the resize operation to validate dimensions and log metadata:

```go
// Validate dimensions using C++ library
if !ValidateDimensions(width, height) {
    return error
}

// Log pixel count and aspect ratio
pixelCount := CalculatePixelCount(width, height)
aspectRatio := CalculateAspectRatio(width, height)
log.Printf("Resizing to %dx%d (pixels: %d, aspect ratio: %.2f)", 
           width, height, pixelCount, aspectRatio)
```

### Building Go with the Library

**Local Development:**
```bash
cd cpp-lib && make all && cd ../go-example
CGO_ENABLED=1 go build -o imgcloud
LD_LIBRARY_PATH=../cpp-lib ./imgcloud
```

**Important:** CGO must be enabled (`CGO_ENABLED=1`) and the shared library path must be in `LD_LIBRARY_PATH`.

## Using the Library in Python

The Python application uses `ctypes` to load and call the C++ shared library.

### Integration

The file `python-example/imgutils.py` provides Python wrappers:

```python
import ctypes
import os

# Load the shared library
lib_path = os.path.join(os.path.dirname(__file__), '..', 'cpp-lib', 'libimgutils.so')
_lib = ctypes.CDLL(lib_path)

# Define function signatures
_lib.calculate_pixel_count.argtypes = [ctypes.c_int, ctypes.c_int]
_lib.calculate_pixel_count.restype = ctypes.c_long

def calculate_pixel_count(width: int, height: int) -> int:
    return _lib.calculate_pixel_count(width, height)
```

### Usage in Code

The Python service uses the library in the resize operation:

```python
import imgutils

# Validate dimensions using C++ library
if not imgutils.validate_dimensions(width, height):
    return error

# Log pixel count and aspect ratio
pixel_count = imgutils.calculate_pixel_count(width, height)
aspect_ratio = imgutils.calculate_aspect_ratio(width, height)
print(f'Resizing to {width}x{height} (pixels: {pixel_count}, aspect ratio: {aspect_ratio:.2f})')
```

### Running Python with the Library

**Local Development:**
```bash
cd cpp-lib && make all && cd ../python-example
LD_LIBRARY_PATH=../cpp-lib python app.py
```

**Important:** The shared library path must be in `LD_LIBRARY_PATH` or copied to a system library directory.

## Multi-Stage Docker Build

A multi-stage Docker build is essential for this project because the C++ library must be compiled first before either the Go or Python applications can be built.

### Build Dependencies

To build the C++ library and applications, you'll need the following tools installed:

**For C++ Library:**
- `g++` - The GNU C++ compiler
- `make` - Build automation tool
- Install on Ubuntu/Debian: `apt-get install g++ make`

**For Go Application:**
- `golang` or `golang-go` - The Go compiler and toolchain
- `g++` - Required for CGO (C bindings)
- `libopencv-dev` - OpenCV development libraries (for GoCV)
- `pkg-config` - Helper tool for compiling with libraries
- Install on Ubuntu/Debian: `apt-get install golang-go g++ libopencv-dev pkg-config`

**For Python Application:**
- `python3` - Python interpreter
- `python3-pip` - Python package manager
- `gcc`, `g++`, `python3-dev` - Required to compile native extensions (NumPy, OpenCV)
- Runtime libraries: `libxcb1`, `libglib2.0-0`, `libsm6`, `libxext6`, `libxrender-dev`, `libgomp1`
- Install on Ubuntu/Debian: `apt-get install python3 python3-pip gcc g++ python3-dev libxcb1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1`

### Build Order

The build process must follow this sequence:

1. **Build C++ Library First**
   - Navigate to the `cpp-lib` directory
   - Run `make all` to build both static and shared libraries
   - This creates `libimgutils.a` and `libimgutils.so`

2. **Build Go Application**
   - The C++ shared library must be available
   - Set `CGO_ENABLED=1` environment variable (required for C bindings)
   - Set `LD_LIBRARY_PATH` to include the cpp-lib directory
   - Build the Go application with `go build`

3. **Install Python Dependencies**
   - The C++ shared library must be available
   - Set `LD_LIBRARY_PATH` to include the cpp-lib directory
   - Install requirements with `pip install -r requirements.txt`

### Making the Library Available

The compiled C++ shared library (`libimgutils.so`) must be accessible at runtime:

**Option 1: Use LD_LIBRARY_PATH**
- Set the environment variable to include the library directory
- Example: `LD_LIBRARY_PATH=/path/to/cpp-lib`
- This is suitable for development and testing

**Option 2: Install to System Library Directory**
- Copy `libimgutils.so` to `/usr/local/lib/`
- Run `ldconfig` to update the library cache (requires root)
- This is suitable for production deployments

**In a Multi-Stage Build:**
- Build stage: All build tools and compile everything
- Runtime stage: Only copy the compiled artifacts and minimal runtime dependencies
- The runtime image should be much smaller since build tools are excluded

### Library Location in Docker Containers

When building Docker images, you need to understand where files are located in the container filesystem:

**Important Considerations:**

1. **The Python Wrapper (`imgutils.py`) Uses Relative Paths**
   - It looks for the library using `os.path.join(os.path.dirname(__file__), '..', 'cpp-lib', 'libimgutils.so')`
   - This means if `imgutils.py` is at `/home/appuser/app/imgutils.py`, it will look for the library at `/home/appuser/cpp-lib/libimgutils.so`
   - The library location must match this relative path expectation

2. **The Go Wrapper (`imgutils.go`) Uses CGO Linking**
   - CGO links the library at compile time using the path specified in `#cgo LDFLAGS`
   - The compiled binary still needs the `.so` file at runtime
   - Use `LD_LIBRARY_PATH` to tell the system where to find it

3. **Multi-Stage Build Requirements**
   - The library must be built in the builder stage (requires `g++` and `make`)
   - The `.so` file must be copied from the builder stage to the runtime stage
   - For Python: The wrapper file (`imgutils.py`) must also be copied to the runtime stage
   - For Go: The `imgutils.go` file is compiled into the binary during the build stage (no separate copy needed)
   - Set `LD_LIBRARY_PATH` in the runtime stage to point to where the `.so` file is located

**Example Directory Structures in Container:**

Python application structure:
```
/home/appuser/
├── app/
│   ├── app.py              # Main application
│   └── imgutils.py         # Python wrapper (looks for ../cpp-lib/libimgutils.so)
└── cpp-lib/
    └── libimgutils.so      # C++ shared library (must be here!)
```

Go application structure:
```
/home/appuser/
├── server                  # Compiled Go binary
└── cpp-lib/
    └── libimgutils.so      # C++ shared library
```

**Key Takeaway:** The location where you copy files in your Dockerfile matters! Make sure:
- The Python wrapper can find the library using its relative path
- The Go binary can find the library via `LD_LIBRARY_PATH`
- All necessary files are copied from the builder stage to the runtime stage

### Don't Forget the Static Directory!

**Important:** Both the Python and Go applications serve a web interface from the `static/` directory at the root endpoint (`/`). If you don't copy this directory into your Docker container, accessing the web UI from outside the container will result in a 404 error.

**For Python Dockerfile:**
```dockerfile
# Copy static directory (needed for the root endpoint to serve index.html)
COPY static /home/appuser/static
```

The Python application uses `os.path.dirname(os.path.dirname(__file__))` to construct the path, which resolves to `/home/appuser/static` when the app is at `/home/appuser/app/app.py`.

**For Go Dockerfile:**
```dockerfile
# Copy static directory to parent directory (needed for the root endpoint to serve index.html)
# The Go code uses ../static/index.html, so we need to place it at /static/
COPY static /static/

# Change ownership to non-root user and static directory
RUN chown -R appuser:appuser /home/appuser && \
    chown -R appuser:appuser /static
```

The Go application uses `../static/index.html` relative to the working directory `/home/appuser`, which resolves to `/static/index.html`.

**Why this matters:** Without the static directory, the application will run successfully, all API endpoints will work, but users trying to access the web interface at `http://your-server:8080/` will get a 404 error. This is easy to miss during development if you only test the API endpoints directly!

### Runtime Dependencies

The final runtime environment needs these libraries:

**For Go Application:**
- OpenCV shared libraries: `libopencv-core`, `libopencv-imgproc`, `libopencv-imgcodecs`
- The version number depends on your Ubuntu version (e.g., `libopencv-core4.6` on Ubuntu 22.04)

**For Python Application:**
- `python3` interpreter
- Runtime libraries for OpenCV: `libxcb1`, `libglib2.0-0`, `libsm6`, `libxext6`, `libxrender-dev`, `libgomp1`
- Python packages will be installed from the build stage

**Both Applications:**
- The `libimgutils.so` shared library
- Set `LD_LIBRARY_PATH` to the directory where you placed the library (e.g., `/home/appuser/cpp-lib` or `/usr/local/lib`)

## Benefits of This Approach

1. **True Multi-Stage Build**: The C++ library *must* be built first, creating a genuine build dependency
2. **Smaller Images**: Build tools (g++, make, etc.) are not in the final image
3. **Code Reuse**: Both Go and Python use the same C++ library, demonstrating FFI (Foreign Function Interface)
4. **Real-World Pattern**: This mimics how production systems often share native libraries across different language runtimes
5. **Learning Objectives**: 
   - CGO for Go
   - ctypes for Python
   - C/C++ interoperability
   - Docker multi-stage builds
   - Library linking and runtime dependencies

## Testing the Integration

### Test C++ Library Directly

```bash
cd cpp-lib
make all
# Verify the libraries were created
ls -l libimgutils.a libimgutils.so
```

### Test Using the Web Interface

Both the Go and Python applications provide a web interface for testing:

1. **Start the Service Locally**
   
   For Python:
   ```bash
   cd cpp-lib && make all && cd ../python-example
   LD_LIBRARY_PATH=../cpp-lib python app.py
   ```
   
   For Go:
   ```bash
   cd cpp-lib && make all && cd ../go-example
   CGO_ENABLED=1 go build -o imgcloud
   LD_LIBRARY_PATH=../cpp-lib ./imgcloud
   ```

2. **Access the Web Interface**
   - Open your browser to `http://localhost:8080`
   - Upload an image using the file selector
   - Select an operation (resize, grayscale, blur, edge detection)
   - For resize: enter width and height values
   - For blur: optionally enter a kernel size (must be odd)
   - Click "Process Image" to see the results
   - Download the processed image if desired

3. **Verify C++ Library Usage**
   - When you resize an image, check the application logs
   - You should see messages showing pixel count and aspect ratio
   - These values come from the C++ library functions

### Test with Command Line (Optional)

You can also test with curl if you prefer:

```bash
# Health check
curl http://localhost:8080/health

# Process an image
curl -F "image=@test.png" -F "operation=resize" -F "width=200" -F "height=200" \
  http://localhost:8080/process -o output.png
```

## Troubleshooting

### Common Issues

1. **"libimgutils.so not found" or "cannot open shared object file"**
   - **Cause**: The system cannot find the `.so` file at runtime
   - **Solution**: 
     - Ensure `LD_LIBRARY_PATH` includes the directory containing `libimgutils.so`
     - Or copy the library to `/usr/local/lib` and run `ldconfig`
     - Verify the library file exists: `ls -l /path/to/libimgutils.so`
     - Check if the library is in the search path: `echo $LD_LIBRARY_PATH`

2. **Go build fails with CGO errors**
   - **Cause**: CGO cannot find the C++ library or headers during compilation
   - **Solution**: 
     - Ensure `CGO_ENABLED=1` is set
     - Verify g++ is installed
     - Check that the library path in `#cgo LDFLAGS` is correct
     - Make sure the library is built before building the Go application

3. **Python can't find the library (FileNotFoundError)**
   - **Cause**: The relative path in `imgutils.py` doesn't match the actual file location
   - **Solution**: 
     - Verify the path in `imgutils.py` resolves correctly
     - Check that `libimgutils.so` exists at the expected location
     - Set `LD_LIBRARY_PATH` before running Python (for dynamic linking)
     - Use Python to debug: `python3 -c "import os; print(os.path.abspath('../cpp-lib/libimgutils.so'))"`

4. **Library functions return incorrect values**
   - **Cause**: Function signatures don't match between the C header and the bindings
   - **Solution**: 
     - Check that the function signatures in the bindings match the C header
     - Verify data type conversions (int, long, double) are correct
     - Review the ctypes documentation for Python or CGO documentation for Go

5. **Docker build fails: "cpp-lib: No such file or directory"**
   - **Cause**: The `cpp-lib` directory is not copied into the Docker build context
   - **Solution**: 
     - Make sure you're running `docker build` from the repository root
     - Verify that `cpp-lib` is not in `.dockerignore`
     - Use the correct build context: `docker build -f path/to/Dockerfile .` (note the `.` at the end)

6. **Docker runtime error: "No module named 'imgutils'"**
   - **Cause**: The wrapper module (`imgutils.py` or `imgutils.go`) was not copied to the runtime stage
   - **Solution**: 
     - Ensure all necessary files are copied from the builder stage
     - For Python: Copy both `app.py` and `imgutils.py`
     - For Go: Include `imgutils.go` in the build command

7. **Web UI returns 404 at root endpoint but API endpoints work**
   - **Cause**: The `static/` directory was not copied into the Docker container
   - **Solution**: 
     - For Python: Add `COPY static /home/appuser/static` to your Dockerfile
     - For Go: Add `COPY static /static/` and update ownership with `chown -R appuser:appuser /static`
     - The static directory contains `index.html` needed for the web interface
     - This is separate from the API endpoints (like `/health`, `/process`) which will work fine without it

### Debugging Tips

**Check if a shared library is loaded:**
```bash
# For a running process
ldd /path/to/executable

# For Python
python3 -c "import ctypes; print(ctypes.CDLL('/path/to/libimgutils.so'))"

# For Go binary
ldd ./server | grep imgutils
```

**Verify library exports:**
```bash
nm -D libimgutils.so | grep calculate_pixel_count
```

**Test library directly:**
```bash
# Build a simple C test program
gcc -o test test.c -L. -limgutils
LD_LIBRARY_PATH=. ./test
```

## Summary

This lab demonstrates a practical multi-stage Docker build where:
- A C++ library is built in the builder stage
- Both Go and Python applications depend on and use this library
- Only the compiled artifacts and runtime dependencies are copied to the final stage
- The resulting image is significantly smaller than a single-stage build
