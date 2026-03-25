# Multi-stage build for Python admin interface
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies in builder stage
COPY python/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application files
COPY python/app.py .
COPY python/db.py .
COPY python/cache.py .
COPY python/endpoints.py .

# Copy static files
COPY static ./static

# Expose port
EXPOSE 8090

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Run the application
CMD ["python", "app.py"]
