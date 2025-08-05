#!/bin/sh
set -e

if [ "${DOCKER_ENTRYPOINT_DEBUG:-0}" = "1" ]; then
  set -x
fi

if [ "$(id -u)" = "0" ]; then
  echo "Running as root - adjusting permissions and switching user"
  
  # Running as root - adjust permissions and switch user
  echo "Adjusting group ID to ${PGID:-1000} for user $USER"
  groupmod -o -g ${PGID:-1000} $USER 2>/dev/null || true
  
  echo "Adjusting user ID to ${PUID:-1000} for user $USER"
  usermod -o -u ${PUID:-1000} $USER 2>/dev/null || true

  if [ -S /var/run/docker.sock ]; then
    echo "Docker socket found - setting ownership to $USER:$USER"
    chown $USER:$USER /var/run/docker.sock
  else
    echo "No Docker socket found at /var/run/docker.sock"
  fi

  echo "Switching to user $USER and executing: $@"
  # Switch to non-root user using sudo
  exec sudo -u $USER "$@"
else
  echo "Running as non-root user - checking Docker socket permissions"
  
  # Running as non-root - just fix Docker socket if needed
  if [ -S /var/run/docker.sock ]; then
    echo "Docker socket found - setting ownership to $USER:$USER"
    sudo chown $USER:$USER /var/run/docker.sock || true
    ls -lha /var/run/docker.sock || true
  else
    echo "No Docker socket found at /var/run/docker.sock"
  fi
  
  echo "Running: $@"
  exec "$@"
fi
