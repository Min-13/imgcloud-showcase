# LAB03 - Image Processing Operations

This document describes the image processing operations supported by the processor service.

## Supported Operations

The image processor supports the following operations:

### Existing Operations
- **resize**: Resize image to specified dimensions (parameters: width, height)
- **grayscale**: Convert image to grayscale
- **blur**: Apply Gaussian blur (parameter: kernel_size, must be odd, default: 5)
- **edge_detection**: Apply Canny edge detection

### New Operations (Lab 03)
- **rotate**: Rotate image by specified angle (parameter: angle in degrees)
- **mirror**: Mirror image horizontally or vertically (parameter: direction - "horizontal" or "vertical")
