# Multi-stage Dockerfile for Flask Status Service

###################################
# Base stage with common setup
###################################
FROM python:3.12-alpine AS base

# Add project label for image cleanup
LABEL project=joyride-dns-service

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set default PUID and PGID
ARG PUID=1000
ARG PGID=1000
ARG USER=appuser
ARG WORKDIR=/app

ENV PUID=$PUID
ENV PGID=$PGID
ENV USER=$USER
ENV WORKDIR=$WORKDIR
ENV UV_LINK_MODE=copy

# Create a non-root user
RUN addgroup -g $PGID $USER && \
    adduser -D -s /bin/sh -u $PUID -G $USER -h /home/$USER $USER && \
    echo "$USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR $WORKDIR

# Install common system dependencies with cache mount
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache \
    curl \
    sudo

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]


###################################
# Development stage
###################################
FROM base AS development

# Install additional development dependencies with cache mount
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache \
    apk-tools-zsh-completion \
    bash \
    bind-tools \
    build-base \
    coreutils \
    docker-cli \
    git \
    github-cli \
    jq \
    linux-headers \
    make \
    openssh-client \
    py3-pip \
    py3-setuptools \
    shadow \
    ssh-import-id \
    zsh \
    zsh-autosuggestions \
    zsh-syntax-highlighting \
    zsh-vcs

# Update user shell to zsh for development
RUN usermod -s /bin/zsh $USER

# Copy requirements files first (for better caching)
COPY pyproject.toml uv.lock ./
COPY swimmies/ ./swimmies/

# Install Python dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_SYSTEM_PYTHON=1 uv sync --extra dev

# Switch to non-root user
USER $USER

# Run the application
# https://code.visualstudio.com/remote/advancedcontainers/start-processes#_adding-startup-commands-to-the-docker-image-instead
CMD [ "sleep", "infinity" ]

###################################
# Production stage
###################################
FROM base AS production

# Copy requirements file first (for better caching)
COPY pyproject.toml uv.lock ./
COPY swimmies/ ./swimmies/

# Install Python dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_SYSTEM_PYTHON=1 uv sync

# Copy application code
COPY app/ ./app/
COPY run.py ./

# Change ownership to user
RUN chown -R $USER:$USER $WORKDIR

# Switch to non-root user
USER $USER

# Run the application using UV script entry point
CMD ["uv", "run", "joyride"]
