/**
 * ImageProcessor - Core image processing operations using OpenCV
 * 
 * This class provides various image processing operations:
 * - resize: Resize image to specified dimensions
 * - grayscale: Convert image to grayscale
 * - blur: Apply Gaussian blur
 * - edge_detection: Apply Canny edge detection
 * - rotate: Rotate image by specified degrees
 * - mirror: Mirror image horizontally or vertically
 */

#ifndef IMAGE_PROCESSOR_H
#define IMAGE_PROCESSOR_H

#include <opencv2/opencv.hpp>
#include <string>

class ImageProcessor {
public:
    /**
     * Process an image with the specified operation and parameters
     * @param image Input image
     * @param operation Operation name
     * @param width Target width (for resize)
     * @param height Target height (for resize)
     * @param kernel_size Kernel size (for blur, must be odd)
     * @param angle Rotation angle in degrees (for rotate)
     * @param direction Mirror direction: "horizontal" or "vertical" (for mirror)
     * @return Processed image
     */
    cv::Mat processImage(const cv::Mat& image, 
                        const std::string& operation,
                        int width = 0, 
                        int height = 0, 
                        int kernel_size = 5,
                        int angle = 0,
                        const std::string& direction = "");

private:
    // Individual operation methods
    cv::Mat resize(const cv::Mat& image, int width, int height);
    cv::Mat grayscale(const cv::Mat& image);
    cv::Mat blur(const cv::Mat& image, int kernel_size);
    cv::Mat edgeDetection(const cv::Mat& image);
    cv::Mat rotate(const cv::Mat& image, int angle);
    cv::Mat mirror(const cv::Mat& image, const std::string& direction);
};

#endif // IMAGE_PROCESSOR_H
