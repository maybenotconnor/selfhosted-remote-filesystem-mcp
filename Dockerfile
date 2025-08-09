# Use Python Alpine for smaller image size
FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    make

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY file_operations.py .
COPY path_validator.py .
COPY auth_config.py .

# Create directories
RUN mkdir -p /data /config

# Create non-root user for security
RUN adduser -D -u 1000 mcp && \
    chown -R mcp:mcp /app /data /config

# Switch to non-root user
USER mcp

# Simple environment defaults
ENV DATA_DIR=/data \
    CONFIG_DIR=/config \
    PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the server
CMD ["python", "server.py"]