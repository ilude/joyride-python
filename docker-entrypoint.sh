#!/bin/bash
set -e

if [ -v DOCKER_ENTRYPOINT_DEBUG ] && [ "$DOCKER_ENTRYPOINT_DEBUG" == 1 ]; then
  set -x
  set -o xtrace
fi

if [ "$(id -u)" = "0" ]; then
  # Running as root - adjust permissions and switch user
  groupmod -o -g ${PGID:-1000} $USER 2>/dev/null || true
  usermod -o -u ${PUID:-1000} $USER 2>/dev/null || true

  if [ -S /var/run/docker.sock ]; then
    chown $USER:$USER /var/run/docker.sock
  fi

  # Switch to non-root user using sudo
  exec sudo -u $USER "$@"
else
  # Running as non-root - just fix Docker socket if needed
  if [ -S /var/run/docker.sock ]; then
    sudo chown $USER:$USER /var/run/docker.sock 2>/dev/null || true
  fi
  
  echo "Running: $@"
  exec "$@"
fi
