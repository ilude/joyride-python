# Swimmies Library Development Setup

This document describes the UV workspace setup for developing the `swimmies` library alongside the `joyride` application.

## Project Structure

```
joyride/
├── pyproject.toml              # Root workspace configuration
├── uv.lock                     # Shared lockfile for entire workspace  
├── app/                        # Main joyride application
│   ├── main.py                 # Uses swimmies library
│   └── ...
├── swimmies/                   # Swimmies library package
│   ├── pyproject.toml         # Library configuration
│   ├── src/
│   │   └── swimmies/
│   │       ├── __init__.py    # Main exports
│   │       ├── core.py        # Core utilities
│   │       └── gossip.py      # Gossip protocol implementation
│   └── tests/
│       ├── test_core.py       # Core functionality tests
│       └── test_gossip.py     # Gossip protocol tests
└── tests/                     # Root project tests
```

## Key Features

✅ **UV Workspace**: Single lockfile for consistent dependencies  
✅ **Editable Installation**: Changes to swimmies are immediately available in joyride  
✅ **No Virtual Environments**: Direct execution in Docker container  
✅ **Proper Testing**: Isolated test suites for both packages  
✅ **Library Structure**: Professional Python package layout  

## Development Workflow

### 1. Making Changes to Swimmies

Edit files in `swimmies/src/swimmies/` - changes are immediately available to joyride:

```bash
cd /workspaces/joyride
# Edit swimmies code...
uv run python -c "import swimmies; swimmies.hello_world()"
```

### 2. Running Tests

Test the swimmies library in isolation:
```bash
uv run --package swimmies pytest swimmies/tests/ -v
```

Test the entire project:
```bash
uv run pytest tests/ -v
```

### 3. Adding Dependencies

Add dependencies to swimmies:
```bash
cd swimmies
uv add requests  # Runtime dependency
uv add --dev black  # Development dependency
```

Add dependencies to joyride:
```bash
cd /workspaces/joyride
uv add fastapi  # Will be available to entire workspace
```

### 4. Using Swimmies in Joyride

```python
# In app/main.py or any joyride module
import swimmies
from swimmies import GossipNode, GossipMessage

# Use library functions
swimmies.hello_world()
node = GossipNode("my-node")
```

## Library Development Best Practices

### Package Structure
- `src/swimmies/__init__.py` - Main exports and version
- `src/swimmies/core.py` - Core utilities  
- `src/swimmies/gossip.py` - Specialized modules
- `tests/` - Comprehensive test coverage

### Version Management
```bash
# Check current version
uv run --package swimmies python -c "import swimmies; print(swimmies.__version__)"

# Update version in swimmies/pyproject.toml, then:
uv sync
```

### Building Distribution
```bash
cd swimmies
uv build  # Creates dist/ with wheel and source distribution
```

## UV Workspace Configuration

### Root `pyproject.toml`
```toml
[project]
name = "joyride"
version = "0.0.1"
dependencies = [
  "swimmies",        # Workspace dependency
  "flask==3.0.0",    # External dependencies
  # ...
]

[tool.uv.sources]
swimmies = { workspace = true }  # Use local workspace version

[tool.uv.workspace]
members = ["swimmies"]           # Include swimmies as workspace member
```

### Library `pyproject.toml` 
```toml
[project]
name = "swimmies"
version = "0.1.0"
description = "Core utilities and gossip protocol for Joyride DNS Service"
dependencies = []                # Library dependencies

[project.scripts]
swimmies = "swimmies:main"      # CLI entry point

[build-system]
requires = ["uv_build>=0.8.4,<0.9.0"]
build-backend = "uv_build"
```

## Advantages of This Setup

1. **Unified Dependencies**: Single lockfile ensures consistent versions across all packages
2. **Fast Development**: Editable installs mean immediate availability of changes
3. **Isolated Testing**: Each package can be tested independently
4. **Professional Structure**: Follows Python packaging best practices
5. **Docker Friendly**: No virtual environment complexity in containers
6. **Scalable**: Easy to add more workspace members as project grows

## Commands Reference

```bash
# Sync entire workspace
uv sync

# Run command in specific workspace member
uv run --package swimmies <command>

# Add dependency to specific member
cd swimmies && uv add <package>

# Run tests for specific member
uv run --package swimmies pytest tests/ -v

# Build library distribution
cd swimmies && uv build

# Import and use library
uv run python -c "import swimmies; swimmies.hello_world()"
```

This setup provides a professional, maintainable foundation for library development within a larger application ecosystem.
