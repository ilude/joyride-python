# Copilot Instructions for Joyride DNS Service

## CRITICAL: Communication Style & Response Format

### Default Behavior: BE BRIEF
- **Complete tasks without verbose explanations** - Action over commentary
- **One sentence summary maximum** unless explicitly requested otherwise
- **Let code and file changes speak for themselves** - no need to describe what was done
- **Only explain when user asks "explain", "why", or "how"**

### Instruction Files Guidelines
- **Keep *.instructions.md files concise** - Essential rules only, no user context
- **Avoid VS Code integration explanations** - Users don't need tool usage details
- **Focus on actionable rules** - What to do, not how to use the file
- **Remove verbose examples** - Keep only necessary code patterns

### Creating .github/instructions/*.instructions.md Files
- **Use specific applyTo patterns** when possible to target exact file types
- **Combine related rules** when applyTo patterns cannot differentiate (e.g., Flask + Python)
- **Create new files only when** applyTo patterns can uniquely target the files
- **Example patterns**: `"**/Dockerfile*"`, `"**/.{gitignore,dockerignore}"`, `"**/*.py"`, `"**/tests/**/*.py"`
- **Avoid overly broad patterns** that would apply to unintended files

### When to Provide Details
- User explicitly asks "explain", "why", or "how"  
- Complex architectural decisions affecting future development
- Breaking changes impacting existing functionality
- Security implications requiring highlighting

### Terminology & Acronyms
- **DRY**: When the user says "DRY", they mean "Don't Repeat Yourself" - the coding best practice of avoiding code duplication by extracting common functionality into reusable components, functions, or modules

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

## Development Workflow

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
- **ALWAYS use `.internal`** for container-generated DNS records
- **NEVER use `.local`** as it conflicts with mDNS/Bonjour services

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
- **`app/`**: Application logic as Python package with `__init__.py` exports
- **`tests/`**: Dedicated test directory using `from app import app` import pattern  
- **`run.py`**: Clean entry point that imports and runs the app
- **Docker Integration**: All containers use `python run.py` as command

### File Organization
```
.
├── .devcontainer/          # Development container config
├── .github/               # GitHub workflows and instructions
├── app/                   # Application source code
├── tests/                 # Test files
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
- Consistent JSON error format with appropriate HTTP status codes
- Include machine-readable error codes and helpful messages

### Logging Standards
- Use JSON format for production logs with appropriate levels
- Include request context, never log sensitive data

## Performance & Monitoring

### Health Check Implementation
- Multiple endpoints: /health (simple), /status (detailed), /ready (readiness)
- Check external dependencies, respond quickly (<1s)
- Support graceful degradation for partial failures

### Metrics & Observability
- Track application metrics (response times, error rates, request counts)
- Include business metrics and distributed tracing with trace IDs

## Security Considerations

### Input Validation
- Validate all inputs at entry points, sanitize for output contexts
- Implement rate limiting and configure CORS appropriately

### Container Security
- Always run as non-root in containers, use minimal Alpine images
- Use Docker secrets or external secret management, minimize exposed ports

## Deployment & Operations

### Production Readiness
- Handle SIGTERM signals properly, set appropriate resource limits
- Support zero-downtime deployments, externalize all configuration

### Monitoring Integration
- Implement comprehensive health checking and metrics export
- Structure logs for centralized systems, define clear alerting rules

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

This document should evolve with the project. Update it when architectural decisions change or new patterns emerge.
