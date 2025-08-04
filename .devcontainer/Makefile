# Development-specific Makefile targets
# This file contains targets that are primarily useful in development environments

# Show help for test commands
help-test:
	@echo "Available test commands:"
	@echo "========================"
	@echo "make test           - Run complete Step 1.2.2 and 1.2.3 test suite with coverage"
	@echo "make test-unit      - Run unit tests only (fast)"  
	@echo "make test-integration - Run integration tests only"
	@echo "make test-verbose   - Run tests with maximum verbosity for debugging"
	@echo "make test-all       - Run ALL working tests (excludes disabled legacy tests)"
	@echo ""

# Initialize development environment
initialize: 
	@echo "Initializing development environment for $(DETECTED_OS)..."
	@echo "HOSTIP: $(HOSTIP)"
	@echo "HOSTIP=$(HOSTIP)" > .devcontainer/.env
	@echo "SEMANTIC_VERSION=$(SEMANTIC_VERSION)" >> .devcontainer/.env
	

# Install development dependencies (only if pyproject.toml changed)
uv.lock:
	uv sync --extra devmake 

# Run just unit tests (fast)
test-unit: uv.lock
	@echo "Running unit tests only..."
	uv run pytest tests/test_injection_config.py tests/test_injection_providers.py tests/test_injection_lifecycle.py -v

# Run integration tests
test-integration: uv.lock
	@echo "Running integration tests..."
	uv run pytest tests/test_step_1_2_2_integration.py -v -s

# Run tests with maximum verbosity for debugging
test-verbose: uv.lock
	@echo "Running tests with maximum verbosity..."
	uv run python -W all -m pytest tests/test_injection_config.py tests/test_injection_providers.py tests/test_injection_lifecycle.py tests/test_step_1_2_2_integration.py --tb=long --capture=no -vvv

# Run ALL tests (including broken ones for debugging)
test: uv.lock
	@echo "Running ALL tests (excluding disabled tests)..."
	uv run python -W all -m pytest tests/ --ignore=tests/disabled --ignore=tests/support --cov=app --cov-report=term-missing --cov-report=html:.htmlcov -v

# Run linting
# E203: whitespace before ':' (conflicts with black formatting)
# W503: line break before binary operator (conflicts with black formatting)
# E501: line too long (disabled to match black's line length handling)
lint: uv.lock
	uv run flake8 app tests --extend-ignore=E203,W503,E501
	@echo "Linting completed successfully!"

# Format code
format: uv.lock
	@echo "Formatting code with black..."
	uv run black app tests 
	@echo "Organizing imports with isort..."
	uv run isort app tests --profile black
	@echo "Removing trailing whitespace..."
	find app tests -name "*.py" -exec sed -i 's/[[:space:]]*$$//' {} \;
	@echo "Code formatting completed!"

# Clean Python cache files
clean:
	@echo "Cleaning Python cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage .htmlcov/ .pytest_cache/ .venv/
	@rm -f /tmp/joyride-dns.pid 2>/dev/null || true
	@echo "Clean completed!"

# Check if application is healthy
health-check:
	@echo "Checking application health..."
	@curl -f http://localhost:5000/health || (echo "❌ Health check failed!" && exit 1)
	@echo "✅ Application is healthy!"

# Show DNS records
dns-status:
	@echo "Current DNS records:"
	@curl -s http://localhost:5000/dns/records | python -m json.tool || echo "❌ Could not fetch DNS records"

# Start Joyride DNS server in background (real target based on PID file)
/tmp/joyride-dns.pid: uv.lock
	uv run joyride &
	@sleep 2


# Stop background Joyride DNS server
stop-app:
	@if [ -f /tmp/joyride-dns.pid ]; then \
		kill -TERM `cat /tmp/joyride-dns.pid` 2>/dev/null || true; \
	fi

# Run Flask application locally
run:
	@FLASK_DEBUG=true uv run joyride

# Start example Docker Compose setup for testing
test-example-up:
	@echo "Starting example Docker Compose setup..."
	docker compose -f docker-compose.example.yml pull 
	docker compose -f docker-compose.example.yml up --force-recreate --remove-orphans -d
	@sleep 3
	@echo "✅ Example setup started!"
	@echo "Access web interface: http://localhost:5000"
	@echo "Example apps:"
	@echo "  - app.example.com (nginx)"
	@echo "  - api.example.com (nginx)"
	@echo "  - api-v1.example.com (nginx)"
	@echo ""
	@echo "Test DNS resolution:"
	@echo "  dig @localhost -p 5353 app.example.com"
	@echo "  dig @localhost -p 5353 api.example.com"

# Stop example Docker Compose setup
test-example-down:
	@echo "Stopping example Docker Compose setup..."
	docker compose -f docker-compose.example.yml down
	@echo "✅ Example setup stopped!"

# Rebuild production image and start with docker-compose.yml
prod-start:
	@echo "Rebuilding production Docker image and starting with docker-compose.yml..."
	docker compose down --remove-orphans || true
	docker compose build 
	docker compose up --force-recreate --remove-orphans -d
	@echo "✅ Production setup started!"
	@echo "Access web interface: http://localhost:5000"
	@echo ""
	@echo "Check status:"
	@echo "  docker compose ps"
	@echo "  docker compose logs -f"

# Stop production Docker Compose setup
prod-down:
	@echo "Stopping production Docker Compose setup..."
	docker compose down --remove-orphans
	@echo "✅ Production setup stopped!"

# Show logs from production setup
prod-logs:
	docker compose logs -f

prod-dump-logs:
	docker compose logs

# Show status of production setup
prod-status:
	@echo "Production Docker Compose Status:"
	@echo "================================="
	docker compose ps
	@echo ""
	@echo "DNS Records:"
	@curl -s http://localhost:5000/dns/records | python -m json.tool 2>/dev/null || echo "❌ Could not fetch DNS records"

# Show logs from example setup
test-example-logs:
	docker compose -f docker-compose.example.yml logs -f

test-dump-logs:
	docker compose -f docker-compose.example.yml logs

# Show status of example setup
test-example-status:
	@echo "Example Docker Compose Status:"
	@echo "=============================="
	docker compose -f docker-compose.example.yml ps
	@echo ""
	@echo "DNS Records:"
	@curl -s http://localhost:5000/dns/records | python -m json.tool 2>/dev/null || echo "❌ Could not fetch DNS records"

# Docker testing commands (requires Docker-in-Docker)
test-docker: uv.lock /tmp/joyride-dns.pid
	@docker run --rm -d --name test-joyride --label joyride.host.name=test.internal nginx:alpine >/dev/null
	@sleep 2
	
	@dig @localhost -p 5353 test.internal +short | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$$' >/dev/null 2>&1 && echo "✅ DNS resolution successful" || echo "❌ DNS resolution failed"
	@curl -s http://localhost:5000/dns/records | grep -q test.internal && echo "✅ API responded with DNS record" || echo "❌ API did not return expected DNS record"

	@docker stop test-joyride >/dev/null 2>&1 || true
	@$(MAKE) --no-print-directory stop-app
	@echo "✅ Docker testing completed!"
