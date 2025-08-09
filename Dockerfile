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

# Create data directory
RUN mkdir -p /data

# Create non-root user for security
RUN adduser -D -u 1000 mcp && \
    chown -R mcp:mcp /app /data

# Switch to non-root user
USER mcp

# Environment variables with defaults
ENV ALLOWED_DIRECTORIES="/data" \
    PORT=8080 \
    HOST=0.0.0.0 \
    ENABLE_WRITE=true \
    JWT_AUDIENCE=filesystem-mcp \
    JWT_ISSUER=filesystem-mcp-server \
    JWT_ALGORITHM=RS256 \
    DISABLE_AUTH=false

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the server
CMD ["python", "server.py"]