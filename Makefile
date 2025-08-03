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
		echo "  stop-bg      - Stop background Joyride DNS server"; \
		echo "  test-docker  - Test Docker integration (requires DinD)"; \
		echo "  test-dns-full- Full DNS resolution test with dig"; \
		echo ""; \
	fi

.env:
	touch .env

build: .env
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


# -------------------------------
# Semantic version bumping logic
# -------------------------------
SEMVER_TAG := $(shell git tag --list 'v*.*.*' --sort=-v:refname | head -n 1)
VERSION := $(shell echo $(SEMVER_TAG) | sed 's/^v//')

define bump_version
  @echo "Latest version: $(SEMVER_TAG)"
  @NEW_VERSION=`echo $(VERSION) | awk -F. 'BEGIN {OFS="."} { \
		if ("$(1)" == "patch") {$3+=1} \
		else if ("$(1)" == "minor") {$2+=1; $3=0} \
		else if ("$(1)" == "major") {$1+=1; $2=0; $3=0} \
		print $1, $2, $3}'` && \
	echo "New version: $$NEW_VERSION" && \
	git tag -a "v$$NEW_VERSION" -m "Release v$$NEW_VERSION" && \
	git push --tags && \
	echo "Tagged and pushed as v$$NEW_VERSION"
endef

bump-patch:
	$(call bump_version,patch)

bump-minor:
	$(call bump_version,minor)

bump-major:
	$(call bump_version,major)

publish: bump-patch
	@git push --all

# Display version and environment info
version:
	@echo "Joyride DNS Service - Development Environment"
	@echo "=============================================="
	@echo "Semantic Version: $(SEMVER_TAG)"
	@if [ "$$USER" != "vscode" ]; then echo "Detected OS: $(DETECTED_OS)"; fi
	@if [ "$$USER" != "vscode" ]; then echo "Container Runtime: $(CONTAINER_RUNTIME)"; fi
	@echo "Host IP: $(HOSTIP)"
	@if [ "$$USER" = "vscode" ]; then echo "$(shell python --version 2>&1)"; fi
	@echo ""
