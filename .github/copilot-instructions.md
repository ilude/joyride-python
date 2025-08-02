# Copilot Instructions for Flask Status Service

## Project Overview
This is a Python Flask microservice that provides a status web page and health check endpoints. It's designed to run in Docker containers with Alpine Linux base images and follows 12-factor app principles for cloud-native deployment.

## Communication Style & Response Format

### Concise Responses
- **Be Brief**: Complete requested tasks without verbose explanations unless explicitly asked, a one or two sentence summary is sufficient and expected.
- **Focus on Action**: Prioritize doing the work over explaining what was done
- **Explain When Asked**: Only provide detailed explanations when the user specifically requests them
- **Code Over Commentary**: Let the code and file changes speak for themselves

### Terminology & Acronyms
- **DRY**: When the user says "DRY", they mean "Don't Repeat Yourself" - the coding best practice of avoiding code duplication by extracting common functionality into reusable components, functions, or modules

### When to Explain
- User explicitly asks "explain", "why", or "how"
- Complex architectural decisions that affect future development
- Breaking changes that might impact existing functionality
- Security implications that need highlighting

## Architecture Principles

### 12-Factor App Compliance
- **Configuration**: All config via environment variables, never hardcoded values
- **Dependencies**: Explicitly declared in requirements files, isolated in containers
- **Stateless**: No local state, horizontally scalable
- **Port Binding**: Self-contained service exports HTTP via port binding
- **Disposability**: Fast startup/shutdown, graceful process termination
- **Dev/Prod Parity**: Keep development and production as similar as possible

### Security First
- Always run containers as non-root users
- Use minimal Alpine Linux base images
- Never expose sensitive data in logs or error messages
- Validate all input, even from trusted sources
- Include health checks for container orchestration

## Coding Standards & Preferences

### Python Best Practices
- **Version**: Use Python 3.12+ features when appropriate
- **Style**: Follow PEP 8 religiously, use Black formatter (line length 88)
- **Function Spacing**: Always use two blank lines before top-level function definitions (PEP 8)
- **Type Hints**: Always include type hints for parameters and return values
- **Error Handling**: Use specific exception types, provide meaningful error messages
- **Logging**: Use Python's logging module, structured logging for production
- **Imports**: Use isort with Black profile, group imports logically

```python
# Good: Type hints and clear error handling
def get_service_status(service_name: str) -> dict[str, Any]:
    try:
        return {"status": "healthy", "service": service_name}
    except ServiceError as e:
        logger.error(f"Service check failed: {e}")
        raise
```

### Flask Development Patterns
- **Application Organization**: Main Flask app is in `app/main.py`, with `app/__init__.py` exporting the app instance
- **Entry Point**: Use `run.py` as the clean entry point for starting the application
- **Blueprint Organization**: When the app grows, group related routes in blueprints within the `app/` directory
- **Configuration Classes**: Use classes for different environment configs, load via `python-dotenv`
- **Error Handling**: Custom error handlers for consistent API responses
- **Request Validation**: Validate inputs early, fail fast with clear messages
- **Response Format**: Consistent JSON structure for API endpoints
- **Package Structure**: Keep the app as a proper Python package with `__init__.py` files

```python
# Preferred error response format
{
    "error": {
        "code": "INVALID_INPUT",
        "message": "Service name is required",
        "details": {"field": "service_name", "value": null}
    }
}
```

### Docker & Containerization
- **Base Images**: Always use Alpine Linux for smaller attack surface
- **Multi-stage Builds**: Use for production to minimize final image size
- **Layer Optimization**: Group RUN commands, clean package caches
- **User Security**: Create and use non-root users in all containers
- **Health Checks**: Include Docker health checks for orchestration
- **Port Exposure**: Only expose necessary ports
- **File Structure**: When copying application files, avoid creating unnecessary nested directories - copy contents directly to the intended location (e.g., `COPY app/ ./` not `COPY app/ ./app/` when WORKDIR is already the target)
- **Package Organization**: Always maintain alphabetical order for packages in RUN apk add commands and requirements.txt files for better maintainability and merge conflict reduction

```dockerfile
# Good: Grouped commands, non-root user, health check
RUN apk add --no-cache curl && \
    rm -rf /var/cache/apk/* && \
    adduser -D -s /bin/sh appuser
USER appuser
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:5000/health
```

### Environment & Configuration
- **Environment Variables**: All configuration via env vars, provide defaults
- **Secrets Management**: Never commit secrets, use Docker secrets or external vaults
- **Environment Files**: Use .env for development, separate files per environment
- **Validation**: Validate configuration at startup, fail fast on invalid config
- **Documentation**: Document all environment variables in README

### Testing Strategy
- **Test Coverage**: Aim for >90% code coverage, focus on critical paths
- **Test Organization**: Tests in dedicated `tests/` directory, separate from application code
- **Test Types**: Unit tests for business logic, integration tests for endpoints
- **Test Structure**: Use pytest fixtures, descriptive test names
- **Import Pattern**: Import app from the package: `from app import app`
- **Mocking**: Mock external dependencies, test in isolation
- **Test Data**: Use factories or fixtures, avoid hardcoded test data
- **Coverage**: Use pytest-cov for coverage reporting: `pytest tests/ --cov=app`

```python
# Good: Descriptive test name, proper fixtures
def test_health_endpoint_returns_correct_status_when_service_is_running(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

# Good: Import pattern for tests
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

## Development Workflow

### Code Quality Tools
- **Formatter**: Black with 88 character line length
- **Import Sorting**: isort with Black profile
- **Linter**: flake8 with appropriate plugins
- **Type Checker**: mypy for static type analysis
- **Security**: bandit for security issue scanning

### Git Practices
- **Commit Messages**: Use conventional commits format
- **Branch Strategy**: Feature branches, main branch protected
- **PR Requirements**: Tests pass, code review, no merge commits
- **Semantic Versioning**: Follow semver for releases

### Development Environment
- **DevContainers**: Use VS Code devcontainers for consistent development
- **Docker Compose**: Profiles for different environments (dev/prod)
- **Hot Reload**: Enable in development for faster iteration
- **Debugging**: Configure proper debugging in devcontainer
- **Shell**: Use zsh with autosuggestions and syntax highlighting; add additional zsh completion libraries as project needs grow

## Future Architecture Considerations

### Gossip Protocol Integration (Planned)
- **Future Enhancement**: Will add gossip protocol support for distributed DNS record synchronization across multiple Joyride DNS instances
- **Design Consideration**: Current architecture should remain flexible for distributed operation - avoid hard coupling between DNS server and record storage
- **State Management**: Consider how current in-memory DNS records will transition to distributed state with eventual consistency
- **Network Communication**: Plan for peer-to-peer communication alongside current Docker event monitoring
- **Conflict Resolution**: Design DNS record management to handle eventual consistency scenarios and record conflicts
- **Service Discovery**: Current single-node Docker monitoring will expand to multi-node gossip-based discovery

When implementing current features, maintain loose coupling and avoid hard dependencies that would complicate future gossip protocol integration. Keep DNS record storage abstracted and network communication patterns flexible.

## Current Project Architecture

### Application Structure
The project follows a clean, package-based organization:

- **`app/`**: Contains all application logic as a proper Python package
  - `__init__.py`: Exports the Flask app instance for easy importing
  - `main.py`: Contains routes, configuration, and application logic
- **`tests/`**: Dedicated test directory with proper package structure
  - Import the app using `from app import app`
  - Run tests with `pytest tests/` for the full test suite
- **`run.py`**: Clean entry point that imports and runs the app
- **Docker Integration**: All containers use `python run.py` as the command

### Entry Point Pattern
```python
# run.py - Application entry point
from app import app

if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
```

### Application Package Pattern
```python
# app/__init__.py - Package exports
from .main import app
__version__ = "1.0.0"

# app/main.py - Application logic
import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
# ... configuration and routes
```

### Testing Integration
- Tests are in separate `tests/` directory
- Use `pytest tests/` to run all tests
- Use `pytest tests/ --cov=app` for coverage reporting
- Import pattern: `from app import app` in test files

## File Organization & Structure

### Project Layout
```
.
├── .devcontainer/          # Development container config
│   ├── devcontainer.json  # VS Code dev container configuration
│   └── Dockerfile         # Development container image
├── .github/               # GitHub specific files (workflows, templates)
│   └── copilot-instructions.md # This file - Copilot context and guidelines
├── app/                   # Application source code
│   ├── __init__.py        # Package initialization, exports Flask app
│   └── main.py            # Main Flask application with routes and logic
├── tests/                 # Test files
│   ├── __init__.py        # Test package initialization
│   └── test_main.py       # Integration and unit tests
├── run.py                 # Application entry point
├── requirements*.txt      # Python dependencies
├── .env*                  # Environment configurations
├── docker-compose.yml     # Multi-environment orchestration
└── Dockerfile            # Production container
```

### Naming Conventions
- **Files**: snake_case for Python files and modules
- **Classes**: PascalCase for class names
- **Functions/Variables**: snake_case for functions and variables
- **Constants**: UPPER_SNAKE_CASE for constants
- **Environment Variables**: UPPER_SNAKE_CASE with service prefix

## Error Handling & Logging

### Error Response Patterns
- **Consistent Structure**: Use consistent JSON error format
- **HTTP Status Codes**: Use appropriate status codes (400, 404, 500, etc.)
- **Error Codes**: Include machine-readable error codes
- **User Messages**: Provide helpful error messages for API consumers

### Logging Standards
- **Structured Logging**: Use JSON format for production logs
- **Log Levels**: Use appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Context**: Include request IDs, user context in logs
- **Security**: Never log sensitive data (passwords, tokens, PII)

## Performance & Monitoring

### Health Check Implementation
- **Multiple Endpoints**: /health (simple), /status (detailed), /ready (readiness)
- **Dependency Checks**: Check external dependencies in detailed health
- **Response Time**: Health checks should respond quickly (<1s)
- **Graceful Degradation**: Partial failures should be reported but not fail health

### Metrics & Observability
- **Application Metrics**: Response times, error rates, request counts
- **Business Metrics**: Service-specific metrics relevant to functionality
- **Infrastructure Metrics**: CPU, memory, disk usage
- **Distributed Tracing**: Include trace IDs for request correlation

## Security Considerations

### Input Validation
- **Validate Early**: Validate all inputs at entry points
- **Sanitization**: Sanitize data for output contexts
- **Rate Limiting**: Implement rate limiting for public endpoints
- **CORS**: Configure CORS appropriately for API endpoints

### Container Security
- **Non-root Users**: Always run as non-root in containers
- **Minimal Images**: Use distroless or Alpine images
- **Secrets**: Use Docker secrets or external secret management
- **Network Security**: Minimize exposed ports, use internal networks

## Deployment & Operations

### Production Readiness
- **Graceful Shutdown**: Handle SIGTERM signals properly
- **Resource Limits**: Set appropriate CPU/memory limits
- **Rolling Updates**: Support zero-downtime deployments
- **Configuration**: Externalize all configuration

### Monitoring Integration
- **Health Checks**: Implement comprehensive health checking
- **Metrics Export**: Export metrics in Prometheus format if needed
- **Log Forwarding**: Structure logs for centralized logging systems
- **Alerting**: Define clear alerting rules for operational issues

## Common Patterns to Follow

### Configuration Management
```python
# Good: Environment-based configuration with validation
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.service_name = os.getenv('SERVICE_NAME', 'Flask Status Service')
        self.port = int(os.getenv('FLASK_PORT', 5000))
        self.debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        self._validate()
    
    def _validate(self):
        if not self.service_name:
            raise ValueError("SERVICE_NAME is required")
```

### API Response Patterns
```python
# Consistent success response
{
    "data": {...},
    "meta": {
        "timestamp": "2025-08-01T12:00:00Z",
        "version": "1.0.0"
    }
}

# Consistent error response  
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": {...}
    }
}
```

## When Making Changes

### Adding New Features
1. Update environment variable documentation
2. Add appropriate tests (unit + integration)
3. Update health check if new dependencies added
4. Consider security implications
5. Update README and API documentation

### Refactoring Guidelines
- Maintain backward compatibility for APIs
- Update tests to match new structure
- Preserve existing environment variable contracts
- Consider migration strategies for breaking changes

### Performance Optimization
- Profile before optimizing
- Maintain readability over micro-optimizations
- Cache appropriately but avoid premature caching
- Monitor resource usage after changes

This document should evolve with the project. Update it when architectural decisions change or new patterns emerge.
