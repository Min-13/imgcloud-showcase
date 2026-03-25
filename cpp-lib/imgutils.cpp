#include "imgutils.h"

extern "C" {

long calculate_pixel_count(int width, int height) {
    return static_cast<long>(width) * static_cast<long>(height);
}

double calculate_aspect_ratio(int width, int height) {
    if (width <= 0 || height <= 0) {
        return 0.0;
    }
    return static_cast<double>(width) / static_cast<double>(height);
}

int validate_dimensions(int width, int height) {
    return (width > 0 && height > 0) ? 1 : 0;
}

}
