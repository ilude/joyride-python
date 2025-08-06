# Copilot Instructions for Joyride DNS Service

## CRITICAL: Communication Style & Response Format

### Default Behavior: BE BRIEF
- **Complete tasks without verbose explanations** - Action over commentary
- **One sentence summary maximum** unless explicitly requested otherwise
- **Let code and file changes speak for themselves** - no need to describe what was done
- **Only explain when user asks "explain", "why", or "how"**
- **Respect file deletions** - If a previously created file is deleted, assume it was intentional and do NOT recreate it
- **Use context7:** Copilot is always allowed and should `use context7` to confirm functionality of software

### File Management Policy
- **Never recreate deleted files** - If a file was previously created by Copilot and later deleted by the user, assume the deletion was intentional
- **Only create new files** when explicitly requested or necessary for a specific user-requested task
- **Respect project structure decisions** - User controls what files should exist in the codebase
- **Store planning, analysis, and working-state markdown files in `.chat_planning`** - when such a markdown file is requested

### Testing and Quality Requirements
- **CRITICAL: Warnings Are Errors** - All warnings during testing must be treated as errors and fixed before any work is considered complete
- **Zero Tolerance for Warnings** - `make test` must run completely clean with no warnings or deprecation messages
- **Modern Standards** - Always use current language syntax and avoid deprecated features

### Terminology & Acronyms
- **DRY**: When the user says "DRY", they mean "Don't Repeat Yourself" - the coding best practice of avoiding code duplication by extracting common functionality into reusable components, functions, or modules

## Architecture Principles

### 12-Factor App Compliance
- **Configuration**: All config via environment variables, never hardcoded values
- **Dependencies**: Explicitly declared in pyproject.toml with UV lockfile, isolated in containers
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
- **Commit Messages**: Use conventional commits format, keep messages concise, avoid long explanations and focus on what was changed. do not use emojis.
- **Branch Strategy**: Feature branches
- **Semantic Versioning**: Follow semver for releases

### Development Environment
- **UV Package Manager**: Use UV for modern Python dependency management and workspace setup
- **DevContainers**: Use VS Code devcontainers for consistent development
- **Docker Compose**: Use `docker compose` (without hyphen) - modern Docker Compose V2 command format
- **Hot Reload**: Enable in development for faster iteration
- **Debugging**: Configure proper debugging in devcontainer
- **Shell**: Use zsh with autosuggestions and syntax highlighting; add additional zsh completion libraries as project needs grow
- **Git Submodules**: swimmies library as independent Git submodule for clean separation
- **ALWAYS use `.internal`** for container-generated DNS records
- **NEVER use `.local`** as it conflicts with mDNS/Bonjour services
- **Swimmies Development**: When working on swimmies library, always `cd /workspaces/joyride/swimmies` first

## Future Architecture Considerations

### Gossip Protocol Integration (Planned)
- **Future Enhancement**: Will add gossip protocol support for distributed DNS record synchronization across multiple Joyride DNS instances
- **Design Consideration**: Current architecture should remain flexible for distributed operation - avoid hard coupling between DNS server and record storage
- **State Management**: Consider how current in-memory DNS records will transition to distributed state with eventual consistency
- **Network Communication**: Plan for peer-to-peer communication alongside current Docker event monitoring
- **Conflict Resolution**: Design DNS record management to handle eventual consistency scenarios and record conflicts
- **Service Discovery**: Current single-node Docker monitoring will expand to multi-node gossip-based discovery
- **Library Integration**: swimmies library provides gossip protocol framework for future distributed features

When implementing current features, maintain loose coupling and avoid hard dependencies that would complicate future gossip protocol integration. Keep DNS record storage abstracted and network communication patterns flexible.

## Current Project Architecture

### Application Structure
- **`app/`**: Application logic as Python package with `__init__.py` exports
- **`tests/`**: Dedicated test directory using `from app import app` import pattern  
- **`run.py`**: Clean entry point that imports and runs the app
- **Docker Integration**: All containers use `python run.py` as command

### File Organization
```
joyride/
├── pyproject.toml              # All dependencies and project config
├── uv.lock                     # Locked dependencies
├── run.py                      # Application entry point
├── DEVELOPMENT.md              # Development guide
├── .devcontainer/              # Development container config
├── .github/                    # GitHub workflows and instructions  
├── app/                        # Application source code
├── swimmies/                   # Git submodule - utility library
├── tests/                      # Test files
├── hosts/                      # Host file configurations
├── .env*                       # Environment configurations
├── docker-compose.yml          # Multi-environment orchestration
└── Dockerfile                  # Production container
```

### Naming Conventions
- **Files**: snake_case for Python files and modules
- **Classes**: PascalCase for class names  
- **Functions/Variables**: snake_case for functions and variables
- **Constants**: UPPER_SNAKE_CASE for constants
- **Environment Variables**: UPPER_SNAKE_CASE with service prefix

## Modern Python Development

### Package Management
- **UV Package Manager**: Use UV exclusively for dependency management
- **pyproject.toml**: All project configuration and dependencies in single file
- **Dependency Groups**: Organize dependencies by purpose (dev, test, lint)
- **Lockfile**: uv.lock ensures reproducible builds across environments
- **No Virtual Environments**: UV handles isolation automatically in containers

### Code Quality Standards
- **Black**: Automatic code formatting (`uv run black app/ tests/ run.py`)
- **isort**: Import sorting (`uv run isort app/ tests/ run.py`)
- **flake8**: Linting (`uv run flake8 app/ tests/ run.py`)
- **Type Hints**: Encouraged for better code documentation
- **Test Coverage**: Maintain >80% coverage with pytest

### Development Commands
```bash
# Install dependencies
uv sync --extra dev

# Run application
uv run python run.py

# Run tests
uv run pytest tests/ -v

# Code quality checks
uv run black app/ tests/ run.py && uv run isort app/ tests/ run.py && uv run flake8 app/ tests/ run.py
```

### Library Integration
- **swimmies Library**: Independent Git submodule at https://github.com/ilude/swimmies
- **Workspace Member**: Configured in pyproject.toml workspace
- **Independent Versioning**: swimmies can evolve separately with own release cycle
- **Core Utilities**: DNS utilities, gossip protocol framework
- **Comprehensive Testing**: Both joyride and swimmies have full test suites

## When Making Changes

### Adding New Features
1. Update environment variable documentation
2. Add appropriate tests (unit + integration)  
3. Update health check if new dependencies added
4. Consider security implications
5. Update README and DEVELOPMENT.md documentation
6. Run code quality checks (`uv run black`, `uv run isort`, `uv run flake8`)

### Adding Dependencies
```bash
# Production dependency
uv add package-name

# Development dependency (add to pyproject.toml dev group)
# Edit pyproject.toml [project.optional-dependencies] section
uv sync --extra dev

# Update lockfile
uv lock --upgrade
```

### Swimmies Library Development
```bash
# Work on swimmies
cd swimmies
# Make changes, test, commit
git add . && git commit -m "feat: add new utility"
git push origin main

# Update joyride to use latest swimmies
cd ..
git submodule update --remote swimmies
uv sync
git add swimmies && git commit -m "chore: update swimmies to latest"
```

### Refactoring Guidelines
- Maintain backward compatibility for APIs
- Update tests to match new structure
- Preserve existing environment variable contracts
- Consider migration strategies for breaking changes
- Use UV commands instead of pip/venv for all Python operations
- Keep swimmies library changes independent from joyride changes

This document should evolve with the project. Update it when architectural decisions change or new patterns emerge.




