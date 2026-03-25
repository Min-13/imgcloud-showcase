/**
 * ImageProcessor implementation
 * Contains all OpenCV-based image processing operations
 */

#include "image_processor.h"
#include <iostream>

cv::Mat ImageProcessor::processImage(const cv::Mat& image, 
                                    const std::string& operation,
                                    int width, 
                                    int height, 
                                    int kernel_size,
                                    int angle,
                                    const std::string& direction) {
    if (operation == "resize") {
        return resize(image, width, height);
    } else if (operation == "grayscale") {
        return grayscale(image);
    } else if (operation == "blur") {
        return blur(image, kernel_size);
    } else if (operation == "edge_detection") {
        return edgeDetection(image);
    } else if (operation == "rotate") {
        return rotate(image, angle);
    } else if (operation == "mirror") {
        return mirror(image, direction);
    } else {
        // Unknown operation - return copy of original
        return image.clone();
    }
}

cv::Mat ImageProcessor::resize(const cv::Mat& image, int width, int height) {
    cv::Mat result;
    // Validate dimensions are within reasonable bounds (max 10000x10000)
    if (width > 0 && height > 0 && width <= 10000 && height <= 10000) {
        // Resize image to specified dimensions using linear interpolation
        cv::resize(image, result, cv::Size(width, height), 0, 0, cv::INTER_LINEAR);
    } else {
        result = image.clone();
    }
    return result;
}

cv::Mat ImageProcessor::grayscale(const cv::Mat& image) {
    cv::Mat result;
    if (image.channels() == 3) {
        // Convert BGR to grayscale, then back to BGR for consistent output format
        cv::Mat gray;
        cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);
        cv::cvtColor(gray, result, cv::COLOR_GRAY2BGR);
    } else {
        result = image.clone();
    }
    return result;
}

cv::Mat ImageProcessor::blur(const cv::Mat& image, int kernel_size) {
    cv::Mat result;
    // Ensure kernel size is odd and positive
    if (kernel_size <= 0 || kernel_size % 2 == 0) {
        kernel_size = 5;
    }
    // Apply Gaussian blur with the specified kernel size
    cv::GaussianBlur(image, result, cv::Size(kernel_size, kernel_size), 0);
    return result;
}

cv::Mat ImageProcessor::edgeDetection(const cv::Mat& image) {
    cv::Mat result;
    cv::Mat gray;
    
    // Convert to grayscale if needed
    if (image.channels() == 3) {
        cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);
    } else {
        gray = image.clone();
    }
    
    // Apply Canny edge detection (thresholds: 100 and 200)
    cv::Mat edges;
    cv::Canny(gray, edges, 100, 200);
    
    // Convert back to BGR for consistent output format
    cv::cvtColor(edges, result, cv::COLOR_GRAY2BGR);
    return result;
}

cv::Mat ImageProcessor::rotate(const cv::Mat& image, int angle) {
    cv::Mat result;
    
    // Normalize angle to 0-360 range to prevent overflow
    int normalized_angle = angle % 360;
    if (normalized_angle < 0) normalized_angle += 360;
    
    // Calculate rotation matrix around image center
    cv::Point2f center(image.cols / 2.0, image.rows / 2.0);
    cv::Mat rotation_matrix = cv::getRotationMatrix2D(center, static_cast<double>(normalized_angle), 1.0);
    
    // Calculate new image bounds to fit the rotated image
    double abs_cos = abs(rotation_matrix.at<double>(0, 0));
    double abs_sin = abs(rotation_matrix.at<double>(0, 1));
    int new_width = int(image.rows * abs_sin + image.cols * abs_cos);
    int new_height = int(image.rows * abs_cos + image.cols * abs_sin);
    
    // Adjust rotation matrix to account for new bounds
    rotation_matrix.at<double>(0, 2) += new_width / 2.0 - center.x;
    rotation_matrix.at<double>(1, 2) += new_height / 2.0 - center.y;
    
    // Apply rotation transformation
    cv::warpAffine(image, result, rotation_matrix, cv::Size(new_width, new_height));
    return result;
}

cv::Mat ImageProcessor::mirror(const cv::Mat& image, const std::string& direction) {
    cv::Mat result;
    std::string dir = direction.empty() ? "horizontal" : direction;
    
    if (dir == "horizontal") {
        // Flip horizontally (around y-axis)
        cv::flip(image, result, 1);
    } else if (dir == "vertical") {
        // Flip vertically (around x-axis)
        cv::flip(image, result, 0);
    } else {
        result = image.clone();
    }
    return result;
}
