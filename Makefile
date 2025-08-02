# Joyride DNS - Development Makefile

.PHONY: help install install-dev test lint format clean build run logs docker-build docker-run docker-stop dev-setup health-check dns-status

# Default target
help:
	@echo "Joyride DNS - Available targets:"
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
	pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/"

# Run linting
lint: .install-dev
	@echo "Running flake8 linting..."
	# E203: whitespace before ':' (conflicts with black formatting)
	# W503: line break before binary operator (conflicts with black formatting)
	flake8 app tests --max-line-length=88 --extend-ignore=E203,W503
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
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -f .install-prod .install-dev
	@echo "Clean completed!"

# Run Flask application locally
run:
	@echo "Starting Joyride DNS server..."
	@echo "Note: DNS server requires elevated privileges (sudo) to bind to port 53"
	python -m app.main

# Show application logs (for when running in background)
logs:
	@echo "Recent application logs:"
	@if [ -f app.log ]; then tail -f app.log; else echo "No log file found. Run 'make run' first."; fi

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t joyride-dns:latest .
	@echo "Docker image built successfully!"

# Run application in Docker
docker-run:
	@echo "Starting Joyride DNS in Docker..."
	docker-compose up -d
	@echo "Application running at http://localhost:5000"
	@echo "DNS server running on port 5353"

# Stop Docker containers
docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "Containers stopped!"

# Full build pipeline (CI/CD)
build: clean .install-dev lint test
	@echo ""
	@echo "✅ Build pipeline completed successfully!"
	@echo "  - Dependencies installed"
	@echo "  - Code linting passed"
	@echo "  - All tests passed"
	@echo ""

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
