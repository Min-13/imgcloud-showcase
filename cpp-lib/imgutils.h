#ifndef IMGUTILS_H
#define IMGUTILS_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Calculate the total number of pixels in an image
 * @param width The width of the image in pixels
 * @param height The height of the image in pixels
 * @return The total number of pixels (width * height)
 */
long calculate_pixel_count(int width, int height);

/**
 * Calculate the aspect ratio of an image
 * @param width The width of the image in pixels
 * @param height The height of the image in pixels
 * @return The aspect ratio as a floating-point number (width / height)
 */
double calculate_aspect_ratio(int width, int height);

/**
 * Validate image dimensions
 * @param width The width of the image in pixels
 * @param height The height of the image in pixels
 * @return 1 if valid (both > 0), 0 otherwise
 */
int validate_dimensions(int width, int height);

#ifdef __cplusplus
}
#endif

#endif // IMGUTILS_H
