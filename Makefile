# https://docs.docker.com/develop/develop-images/build_enhancements/
# https://www.docker.com/blog/faster-builds-in-compose-thanks-to-buildkit-support/
export DOCKER_BUILDKIT := 1
export DOCKER_SCAN_SUGGEST := false
export COMPOSE_DOCKER_CLI_BUILD := 1

# Include development targets if available
-include .devcontainer/Makefile

# Cross-platform detection
ifeq ($(OS),Windows_NT)
	DETECTED_OS := windows
	SHELL_CMD := powershell
	ifneq (, $(shell where pwsh 2>nul))
		SHELL_CMD := pwsh
	endif
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		DETECTED_OS := linux
	endif
	ifeq ($(UNAME_S),Darwin)
		DETECTED_OS := macos
	endif
endif
INITIALIZER := initialize-$(DETECTED_OS)

# Host IP detection (simplified for devcontainer)
ifndef HOSTIP
	ifeq ($(DETECTED_OS),linux)
		# In devcontainer/Docker, get the host gateway IP (Docker host)
		HOSTIP := $(shell ip route get 1 | head -1 | awk '{print $$7}' )
	else ifeq ($(DETECTED_OS),macos)
		HOSTIP := $(shell ifconfig | grep "inet " | grep -Fv 127.0.0.1 | awk '{print $$2}' )
	else ifeq ($(DETECTED_OS),windows)
		HOSTIP := $(shell powershell -noprofile -command '(Get-NetIPConfiguration | Where-Object {$$_.IPv4DefaultGateway -ne $$null -and $$_.NetAdapter.Status -ne "Disconnected"}).IPv4Address.IPAddress' )
	endif
endif

# Container runtime detection
ifndef CONTAINER_RUNTIME
	ifneq (, $(shell which podman 2>/dev/null))
		CONTAINER_RUNTIME := podman
	else
		CONTAINER_RUNTIME := docker
	endif
endif

# Export variables
export HOSTIP
export CONTAINER_RUNTIME
export DETECTED_OS



.PHONY: help build run start up down restart docker-clean

# help target
help:
	@echo "Available targets:"
	@echo "Detected OS: $(DETECTED_OS), Container Runtime: $(CONTAINER_RUNTIME), Host IP: $(HOSTIP)"
	@echo ""
	@echo "Application:"
	@echo "  run          - Run the Flask application locally"
	@echo ""
	@echo "Docker:"
	@echo "  build        - Build Docker image"
	@echo "  start        - Start application in Docker (detached)"
	@echo "  up           - Start application in Docker (foreground)"
	@echo "  down         - Stop Docker containers"
	@echo "  restart      - Restart Docker containers"
	@echo "  docker-clean - Clean up Docker containers and images"
	@echo ""
	@if [ -f .devcontainer/Makefile ]; then \
		echo "Development (available in devcontainer):"; \
		echo "  version      - Display version and environment info"; \
		echo "  initialize   - Initialize development environment"; \
		echo "  test         - Run tests with coverage"; \
		echo "  lint         - Run linting (flake8)"; \
		echo "  format       - Format code (black, isort)"; \
		echo "  clean        - Clean Python cache files"; \
		echo "  health-check - Check application health"; \
		echo "  dns-status   - Show current DNS records"; \
		echo ""; \
	fi


# Display version and environment info
version:
	@echo "Joyride DNS Service - Development Environment"
	@echo "=============================================="
	@echo "Detected OS: $(DETECTED_OS)"
	@echo "Container Runtime: $(CONTAINER_RUNTIME)"
	@echo "Host IP: $(HOSTIP)"
	@echo "Python: $(shell python --version 2>&1)"
	@echo ""

# Run Flask application locally
run:
	@echo "Starting Joyride DNS server..."
	python -m app.main


build:
	$(CONTAINER_RUNTIME) compose build


start: build
	$(CONTAINER_RUNTIME) compose up --force-recreate --remove-orphans -d


up: build 
	$(CONTAINER_RUNTIME) compose up --force-recreate --abort-on-container-exit --remove-orphans


down:
	$(CONTAINER_RUNTIME) compose down


restart: build down start


docker-clean:
	$(CONTAINER_RUNTIME) compose down --volumes --remove-orphans --rmi local
	$(CONTAINER_RUNTIME) compose rm -f
	-$(CONTAINER_RUNTIME) image rm -f $(shell $(CONTAINER_RUNTIME) image ls -q --filter label=project=joyride-dns-service)


