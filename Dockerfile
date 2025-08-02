# Multi-stage Dockerfile for Flask Status Service

# Development stage
FROM python:3.12-alpine AS development

# Install system dependencies for development
RUN apk add --no-cache \
    bash \
    build-base \
    curl \
    git \
    linux-headers \
    openssh-client \
    sudo \
    zsh \
    zsh-autosuggestions \
    zsh-syntax-highlighting \
    && rm -rf /var/cache/apk/*

# Create a non-root user
RUN addgroup -g 1000 vscode && \
    adduser -D -s /bin/zsh -u 1000 -G vscode -h /home/vscode vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /workspace

# Copy requirements files
COPY requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt

# Change ownership of workspace to vscode user
RUN chown -R vscode:vscode /workspace

# Switch to non-root user
USER vscode

# Expose Flask development port
EXPOSE 5000

# Default command for development
CMD ["python", "run.py"]

# Production stage
FROM python:3.12-alpine AS production

# Install system dependencies
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Create a non-root user for security
RUN addgroup -g 1000 appuser && \
    adduser -D -s /bin/sh -u 1000 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "main.py"]
