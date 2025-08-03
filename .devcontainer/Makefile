# Development-specific Makefile targets
# This file contains targets that are primarily useful in development environments

# Initialize development environment
initialize: $(INITIALIZER)
	@echo "Initializing development environment for $(DETECTED_OS)..."
	@echo "HOSTIP: $(HOSTIP)"
	@sed -i '/^HOSTIP=/d; $$a HOSTIP=$(HOSTIP)' .env 2>/dev/null || echo "HOSTIP=$(HOSTIP)" > .env

initialize-linux:
	

initialize-macos:
	

initialize-windows:

# Install development dependencies (only if requirements-dev.txt changed)
.install-dev: requirements-dev.txt
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	@touch .install-dev

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
	flake8 app tests --extend-ignore=E203,W503,E501
	@echo "Linting completed successfully!"

# Format code
format: .install-dev
	@echo "Formatting code with black..."
	black app tests 
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

# Check if application is healthy
health-check:
	@echo "Checking application health..."
	@curl -f http://localhost:5000/health || (echo "❌ Health check failed!" && exit 1)
	@echo "✅ Application is healthy!"

# Show DNS records
dns-status:
	@echo "Current DNS records:"
	@curl -s http://localhost:5000/dns/records | python -m json.tool || echo "❌ Could not fetch DNS records"
