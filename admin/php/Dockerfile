# Multi-stage build for PHP admin interface
FROM php:8.2-cli as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    git \
    && docker-php-ext-install pdo pdo_pgsql \
    && git clone https://github.com/phpredis/phpredis.git /usr/src/php/ext/redis \
    && docker-php-ext-install redis \
    && rm -rf /var/lib/apt/lists/*

# Final stage
FROM php:8.2-cli

# Copy extensions from builder
COPY --from=builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

# Copy application files
COPY php/index.php .
COPY php/db.php .
COPY php/cache.php .
COPY php/endpoints.php .

# Copy static files
COPY static ./static

# Expose port
EXPOSE 8090

# Run PHP built-in server
CMD ["php", "-S", "0.0.0.0:8090"]
