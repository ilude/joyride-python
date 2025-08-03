---
description: "Python coding standards and best practices for Joyride DNS Service"
applyTo: "**/*.py"
---

# Python Development Standards

### Code Style
- Follow PEP 8 with Black formatter (line length 88)
- Two blank lines before top-level function definitions
- **Strong type hints** for all parameters and return values
- **Use Pydantic** for data validation and serialization whenever possible
- Use isort with Black profile for imports

### Type Safety
- Prefer Pydantic models over plain dictionaries for structured data
- Use generic types (`list[str]`, `dict[str, Any]`) over legacy forms
- Leverage `typing` module for complex types (`Union`, `Optional`, `Literal`)
- Use dataclasses for simple data containers when Pydantic is overkill

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Use Python's logging module with structured logging

### Example Pattern
```python
from pydantic import BaseModel
from typing import Any

class ServiceStatus(BaseModel):
    status: str
    service: str
    timestamp: str
    details: dict[str, Any] | None = None

def get_service_status(service_name: str) -> ServiceStatus:
    try:
        return ServiceStatus(
            status="healthy", 
            service=service_name,
            timestamp=datetime.now().isoformat()
        )
    except ServiceError as e:
        logger.error(f"Service check failed: {e}")
        raise
```

### Configuration
- Use classes for environment configs
- Load via `python-dotenv` for development
- Use `os.getenv()` with sensible defaults
- Separate development and production configurations

### Network Services & Background Processing
- Use threading for background services (DNS server, Docker monitoring)
- Implement proper signal handling for graceful shutdown
- Use threading.Lock for shared resources
- Create PID files for process management in `/tmp/` for development
- Use proper cleanup with `atexit.register()`

### Flask Applications
- Structure with `app/` package using `__init__.py` exports
- Use `run.py` as clean entry point
- Disable debug mode for background processes (`FLASK_DEBUG=false`)
- Implement health check endpoints (`/health`, `/status`)
- Use Pydantic for API response models

### Service Integration Patterns
```python
# Signal handling for services
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    cleanup_services()
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```
- Load via `python-dotenv`
- Validate configuration at startup

### Package Structure
- Keep app as proper Python package with `__init__.py` files
- Import pattern: `from app import app`
- Custom error handlers for consistent API responses
- Validate inputs early, fail fast with clear messages

### Code Quality Tools
- Black formatter (88 character line length)
- isort with Black profile
- flake8 linter
- mypy for type checking
- bandit for security scanning



## Flask Application Patterns

### Application Organization
- Main Flask app in `app/main.py`
- Export app instance via `app/__init__.py`
- Use `run.py` as clean entry point
- Blueprint organization for route grouping



### API Response Format
```python
# Success response
{
    "data": {...},
    "meta": {
        "timestamp": "2025-08-01T12:00:00Z",
        "version": "1.0.0"
    }
}

# Error response
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": {...}
    }
}
```
