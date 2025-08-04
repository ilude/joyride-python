# Joyride DNS Service - Development Guide

Modern Python development setup using UV and pyproject.toml for the Joyride DNS service with integrated swimmies library.

## Project Structure

```
joyride/
├── pyproject.toml              # All dependencies and project config
├── run.py                      # Application entry point
├── uv.lock                     # Locked dependencies
├── app/                        # Main application code
├── swimmies/                   # Git submodule - utility library
├── tests/                      # Test suite
└── hosts/                      # Host file configurations
```

## Quick Start

### Prerequisites
- Python 3.12+
- UV package manager
- Docker (for development)

### Setup

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/ilude/joyride-python.git
cd joyride-python

# Install dependencies
uv sync

# Install with development tools
uv sync --extra dev

# Run the application
uv run python run.py
```

## Dependencies

All dependencies are managed in `pyproject.toml`:

### Production Dependencies
- `swimmies` - Utility library (workspace)
- `dnslib==0.9.24` - DNS protocol implementation
- `docker==7.1.0` - Docker API client
- `flask==3.0.0` - Web framework
- `gunicorn==21.2.0` - WSGI server
- `pydantic==2.8.2` - Data validation
- `python-dotenv==1.0.0` - Environment variables

### Development Dependencies

Install with: `uv sync --extra dev`

**Code Quality (`--extra lint`)**
- `black==23.12.1` - Code formatter
- `flake8==7.0.0` - Linter  
- `isort==5.13.2` - Import sorter

**Testing (`--extra test`)**
- `pytest==7.4.3` - Test framework
- `pytest-flask==1.3.0` - Flask testing utilities
- `pytest-cov==4.1.0` - Coverage reporting

## Development Workflow

### Running the Application

```bash
# Development mode
uv run python run.py

# With environment variables
DNS_PORT=5353 WEB_PORT=5000 uv run python run.py
```

### Code Quality

```bash
# Format code
uv run black app/ tests/ run.py

# Sort imports  
uv run isort app/ tests/ run.py

# Lint code
uv run flake8 app/ tests/ run.py

# All quality checks
uv run black app/ tests/ run.py && \
uv run isort app/ tests/ run.py && \
uv run flake8 app/ tests/ run.py
```

### Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_main.py -v

# Run tests in swimmies library
uv run --package swimmies pytest swimmies/tests/ -v
```

### Swimmies Library Development

The swimmies library is a Git submodule with independent versioning:

```bash
# Develop swimmies
cd swimmies
# Edit files...
git add . && git commit -m "Add feature"
git push origin main

# Update joyride to use latest swimmies
cd ..
git add swimmies && git commit -m "Update swimmies"
git push origin main

# Update submodule to latest
git submodule update --remote swimmies
uv sync
```

## Dependency Management

### Adding Dependencies

```bash
# Add production dependency
uv add requests

# Add development dependency
uv add --dev mypy

# Add to specific group
# Edit pyproject.toml and add to appropriate [project.optional-dependencies] section
uv sync --extra dev
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package flask

# Sync after updates
uv sync --extra dev
```

### Dependency Groups

Install specific dependency groups:

```bash
# Production only
uv sync

# With development tools
uv sync --extra dev

# Testing only
uv sync --extra test

# Linting only  
uv sync --extra lint

# Multiple groups
uv sync --extra dev --extra test
```

## Docker Development

The project includes Docker configurations for consistent development:

```bash
# Build development image
docker build -t joyride-dev .

# Run with Docker Compose
docker-compose up --build

# Development with hot reload
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

## Configuration

Configuration is managed through environment variables and `.env` files:

```bash
# Copy example configuration
cp .env.example .env

# Key variables
DNS_PORT=5353           # DNS server port
WEB_PORT=5000          # Web interface port  
HOST=0.0.0.0           # Bind address
DEBUG=false            # Debug mode
```

## Project Metadata

The project is configured with proper Python packaging metadata:

- **License**: MIT
- **Python**: >=3.12
- **Keywords**: dns, docker, networking, devops
- **Repository**: https://github.com/ilude/joyride-python

## Best Practices

### Code Style
- Use `black` for formatting (automatic)
- Use `isort` for import sorting  
- Follow `flake8` linting rules
- Type hints encouraged (future: add `mypy`)

### Testing
- Write tests for all new features
- Maintain >80% test coverage
- Use pytest fixtures for common test data
- Test both positive and negative cases

### Git Workflow
- Feature branches for new development
- Conventional commit messages
- Keep submodule (swimmies) updated
- Squash commits before merging

### Dependencies
- Pin exact versions for stability
- Use optional dependency groups
- Document dependency choices
- Regular security updates

This setup provides a modern, maintainable foundation for Python development with excellent tooling integration and clear separation of concerns.
