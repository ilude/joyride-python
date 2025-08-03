# https://docs.docker.com/develop/develop-images/build_enhancements/
# https://www.docker.com/blog/faster-builds-in-compose-thanks-to-buildkit-support/
export DOCKER_BUILDKIT := 1
export DOCKER_SCAN_SUGGEST := false
export COMPOSE_DOCKER_CLI_BUILD := 1

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

.PHONY: help install install-dev test lint format clean build run logs docker-build docker-run docker-stop dev-setup health-check dns-status version initialize initialize-linux initialize-macos initialize-windows

# Initialize development environment
initialize: $(INITIALIZER)
	@echo "Initializing development environment for $(DETECTED_OS)..."
	@echo "HOSTIP: $(HOSTIP)"
	@sed -i '/^HOSTIP=/d; $$a HOSTIP=$(HOSTIP)' .env 2>/dev/null || echo "HOSTIP=$(HOSTIP)" > .env

initialize-linux:
	

initialize-macos:
	

initialize-windows:

# Display version and environment info
version:
	@echo "Joyride DNS Service - Development Environment"
	@echo "=============================================="
	@echo "Detected OS: $(DETECTED_OS)"
	@echo "Container Runtime: $(CONTAINER_RUNTIME)"
	@echo "Host IP: $(HOSTIP)"
	@echo "Python: $(shell python --version 2>&1)"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not available')"
	@echo ""

# help target
help:
	@echo "Available targets:"
	@echo "Detected OS: $(DETECTED_OS), Container Runtime: $(CONTAINER_RUNTIME), Host IP: $(HOSTIP)"
	@echo ""
	@echo "Setup:"
	@echo "  version      - Display version and environment info"
	@echo "  initialize   - Initialize development environment"
	@echo ""
	@echo "Development:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linting (flake8)"
	@echo "  format       - Format code (black, isort)"
	@echo "  clean        - Clean Python cache files"
	@echo ""
	@echo "Application:"
	@echo "  run          - Run the Flask application locally"
	@echo "  logs         - Show application logs"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run application in Docker"
	@echo "  docker-stop  - Stop Docker containers"
	@echo ""
	@echo "CI/CD:"
	@echo "  build        - Full build pipeline (install, lint, test)"
	@echo ""

# Install production dependencies (only if requirements.txt changed)
.install-prod: requirements.txt
	@echo "Installing production dependencies..."
	pip install -r requirements.txt
	@touch .install-prod

# Install development dependencies (only if requirements-dev.txt changed)
.install-dev: requirements-dev.txt
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	@touch .install-dev

# Convenience targets
install: .install-prod

install-dev: .install-dev

# Run tests with coverage
test: .install-dev
	@echo "Running tests with coverage..."
	pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:.htmlcov


# Run linting
lint: .install-dev
	@echo "Running flake8 linting..."
	# E203: whitespace before ':' (conflicts with black formatting)
	# W503: line break before binary operator (conflicts with black formatting)
	# E501: line too long (disabled to match black's line length handling)
	flake8 app tests --max-line-length=88 --extend-ignore=E203,W503,E501
	@echo "Linting completed successfully!"

# Format code
format: .install-dev
	@echo "Formatting code with black..."
	black app tests --line-length=88
	@echo "Organizing imports with isort..."
	isort app tests --profile black
	@echo "Removing trailing whitespace..."
	find app tests -name "*.py" -exec sed -i 's/[[:space:]]*$$//' {} \;
	@echo "Code formatting completed!"

# Clean Python cache files
clean:
	@echo "Cleaning Python cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage .htmlcov/ .pytest_cache/
	rm -f .install-prod .install-dev
	@echo "Clean completed!"

# Run Flask application locally
run:
	@echo "Starting Joyride DNS server..."
	python -m app.main

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	@echo "Detected HOSTIP: $(HOSTIP)"
	HOSTIP=$(HOSTIP) docker build -t joyride-dns:latest .
	@echo "Docker image built successfully!"

# Run application in Docker
docker-run:
	@echo "Starting Joyride DNS in Docker..."
	@echo "Detected HOSTIP: $(HOSTIP)"
	HOSTIP=$(HOSTIP) docker-compose up -d
	@echo "Application running at http://localhost:5000"
	@echo "DNS server running on port 5353"
	@echo "DNS records will point to: $(HOSTIP)"

# Stop Docker containers
docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "Containers stopped!"

# Full build pipeline (CI/CD)
build: clean .install-dev lint test
	@echo ""
	@echo "✅ Build pipeline completed successfully!"


# Development setup (one-time setup for new developers)
dev-setup: .install-dev
	@echo "Setting up development environment..."
	@echo "Installing pre-commit hooks..."
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
		echo "Pre-commit hooks installed!"; \
	else \
		echo "pre-commit not found. Install with: pip install pre-commit"; \
	fi
	@echo ""
	@echo "🎉 Development environment setup complete!"
	@echo ""
	@echo "Quick start:"
	@echo "  make test    - Run tests"
	@echo "  make run     - Start the application"
	@echo "  make help    - Show all available targets"
	@echo ""

# Check if application is healthy
health-check:
	@echo "Checking application health..."
	@curl -f http://localhost:5000/health || (echo "❌ Health check failed!" && exit 1)
	@echo "✅ Application is healthy!"

# Show DNS records
dns-status:
	@echo "Current DNS records:"
	@curl -s http://localhost:5000/dns/records | python -m json.tool || echo "❌ Could not fetch DNS records"
