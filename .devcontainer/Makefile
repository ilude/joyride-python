# Development-specific Makefile targets
# This file contains targets that are primarily useful in development environments

# Initialize development environment
initialize: 
	@echo "Initializing development environment for $(DETECTED_OS)..."
	@echo "HOSTIP: $(HOSTIP)"
	@echo "HOSTIP=$(HOSTIP)" > .devcontainer/.env
	@echo "SEMANTIC_VERSION=$(SEMANTIC_VERSION)" >> .devcontainer/.env
	

# Install development dependencies (only if pyproject.toml changed)
uv.lock:
	uv sync --extra dev

# Run tests with coverage
test: uv.lock
	@echo "Running tests with coverage..."
	uv run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:.htmlcov

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


# Docker testing commands (requires Docker-in-Docker)
test-docker: uv.lock /tmp/joyride-dns.pid
	@docker run --rm -d --name test-joyride --label joyride.host.name=test.internal nginx:alpine >/dev/null
	@sleep 2
	
	@dig @localhost -p 5353 test.internal +short | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$$' >/dev/null 2>&1 && echo "✅ DNS resolution successful" || echo "❌ DNS resolution failed"
	@curl -s http://localhost:5000/dns/records | grep -q test.internal && echo "✅ API responded with DNS record" || echo "❌ API did not return expected DNS record"

	@docker stop test-joyride >/dev/null 2>&1 || true
	@$(MAKE) --no-print-directory stop-app
	@echo "✅ Docker testing completed!"
