---
description: "Dockerfile and containerization best practices for Joyride DNS Service"
applyTo: "**/Dockerfile*"
---

## Docker & Containerization Best Practices

### Base Images
- **Always use Alpine Linux** for smaller attack surface and reduced image size
- Use specific Alpine version tags for reproducible builds
- Prefer official Alpine-based images when available

### Multi-stage Builds
- **Use multi-stage builds** for production to minimize final image size
- Separate build dependencies from runtime dependencies
- Copy only necessary artifacts to final stage

### Layer Optimization
- **Group RUN commands** to reduce layer count and image size
- **Clean package caches** in the same RUN command to avoid cache layers
- Order commands from least to most frequently changing for better cache utilization

### User Security
- **Create and use non-root users** in all containers
- Use `adduser -D -s /bin/sh username` for Alpine Linux
- Set appropriate USER directive before EXPOSE and CMD

### Health Checks
- **Include Docker health checks** for container orchestration
- Use lightweight health check commands (curl, wget, or custom scripts)
- Set appropriate intervals and timeouts for your service

### Port Exposure
- **Only expose necessary ports** - do not expose internal service ports
- Document exposed ports in comments
- Use environment variables for configurable ports

### File Structure & Copying
- **Avoid unnecessary nested directories** when copying application files
- Copy contents directly to intended location: `COPY app/ ./` not `COPY app/ ./app/`
- Use .dockerignore to exclude unnecessary files
- Copy requirements files separately for better layer caching

### Package Organization
- **Maintain alphabetical order** for packages in `RUN apk add` commands
- **Maintain alphabetical order** in requirements.txt files
- This improves maintainability and reduces merge conflicts

### Environment Variables
- **Use ARG for build-time variables** (PUID, PGID, USER, WORKDIR)
- **Use ENV for runtime variables** that containers need
- Provide sensible defaults for all variables
- Document all environment variables

## Example Dockerfile Pattern

```dockerfile
# Multi-stage build example
FROM python:3.12-alpine AS base

# Build arguments for flexibility
ARG PUID=1000
ARG PGID=1000
ARG USER=appuser
ARG WORKDIR=/app

# Create user and set up directories
RUN addgroup -g ${PGID} ${USER} && \
    adduser -D -u ${PUID} -G ${USER} -s /bin/sh ${USER} && \
    mkdir -p ${WORKDIR} && \
    chown -R ${USER}:${USER} ${WORKDIR}

WORKDIR ${WORKDIR}

# Development stage
FROM base AS development
RUN apk add --no-cache \
    curl \
    git \
    github-cli
USER ${USER}

# Production stage  
FROM base AS production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./
USER ${USER}
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:5000/health || exit 1
CMD ["python", "run.py"]
```

## Common Patterns

### Package Installation
```dockerfile
# Good: Grouped, cached, cleaned
RUN apk add --no-cache \
    curl \
    git \
    wget && \
    rm -rf /var/cache/apk/*
```

### Python Dependencies
```dockerfile
# Good: Separate copy for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./
```

### User Creation
```dockerfile
# Good: Flexible user creation
ARG PUID=1000
ARG PGID=1000
ARG USER=appuser
RUN addgroup -g ${PGID} ${USER} && \
    adduser -D -u ${PUID} -G ${USER} -s /bin/sh ${USER}
```

### Health Checks
```dockerfile
# Good: Specific endpoint check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
    CMD curl -f http://localhost:5000/health || exit 1
```

## Security Considerations

### Non-root Execution
- Never run containers as root in production
- Create specific users for application processes
- Use USER directive before CMD/ENTRYPOINT

### Minimal Attack Surface
- Use Alpine Linux base images
- Only install necessary packages
- Remove build dependencies in multi-stage builds
- Use .dockerignore to exclude sensitive files

### Secret Management
- Never include secrets in Dockerfile or layers
- Use Docker secrets or external secret management
- Use build args for non-sensitive build-time configuration

## BuildKit Features

### Cache Mounts
```dockerfile
# Use BuildKit cache mounts for package managers
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache python3 py3-pip

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Multi-platform Builds
```dockerfile
# Support multiple architectures
FROM --platform=$BUILDPLATFORM python:3.12-alpine AS base
```
