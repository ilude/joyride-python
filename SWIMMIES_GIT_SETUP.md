# Git Submodule Setup for Swimmies

This document explains how to set up swimmies as a separate Git repository while keeping it available for development in the joyride workspace.

## Current Setup

1. **Swimmies Repository**: `/workspaces/swimmies-repo` - Independent Git repository
2. **Joyride Workspace**: `/workspaces/joyride/swimmies` - Copy for development
3. **UV Workspace**: Configured to use local swimmies for development

## Setting Up Remote Repository

### Option 1: GitHub Repository (Recommended)

1. **Create GitHub repository for swimmies**:
   ```bash
   # On GitHub, create new repository named 'swimmies'
   ```

2. **Push swimmies to GitHub**:
   ```bash
   cd /workspaces/swimmies-repo
   git remote add origin https://github.com/ilude/swimmies.git
   git branch -M main
   git push -u origin main
   ```

3. **Replace local copy with submodule**:
   ```bash
   cd /workspaces/joyride
   rm -rf swimmies
   git submodule add https://github.com/ilude/swimmies.git swimmies
   git add .gitmodules swimmies
   git commit -m "Add swimmies as Git submodule"
   ```

### Option 2: Local Development Only

If you want to keep it local for now, the current setup works:

```bash
cd /workspaces/joyride
# swimmies/ directory contains the library
# You can develop directly in this directory
# When ready, push changes to swimmies-repo:
cp -r swimmies/* /workspaces/swimmies-repo/
cd /workspaces/swimmies-repo
git add . && git commit -m "Update from development"
```

## Development Workflow

### With Git Submodule (After GitHub setup)

1. **Clone joyride with submodules**:
   ```bash
   git clone --recurse-submodules https://github.com/ilude/joyride-python.git
   cd joyride-python
   uv sync
   ```

2. **Update submodule to latest**:
   ```bash
   git submodule update --remote swimmies
   uv sync  # Re-sync after submodule update
   ```

3. **Develop swimmies**:
   ```bash
   cd swimmies
   # Make changes...
   git add . && git commit -m "Add feature"
   git push origin main
   
   cd ..
   git add swimmies  # Update submodule reference
   git commit -m "Update swimmies to latest version"
   ```

### Current Local Development

```bash
cd /workspaces/joyride
# Edit files in swimmies/
uv run python -c "import swimmies; swimmies.hello_world()"

# Test changes
uv run --package swimmies pytest swimmies/tests/ -v

# When ready, sync to main repo
cp -r swimmies/* /workspaces/swimmies-repo/
cd /workspaces/swimmies-repo
git add . && git commit -m "Development updates"
```

## UV Workspace Configuration

The current `pyproject.toml` is configured to work with both approaches:

```toml
[tool.uv.workspace]
members = ["swimmies"]

[tool.uv.sources]
swimmies = { workspace = true }
```

This allows:
- ✅ Editable installs during development
- ✅ Unified dependency management
- ✅ Independent library versioning
- ✅ Separate Git history for swimmies

## Advantages of This Setup

1. **Independent Versioning**: Swimmies has its own version and release cycle
2. **Reusable Library**: Can be used in other projects
3. **Development Convenience**: Still available as workspace member
4. **Clean Separation**: Clear boundary between library and application
5. **GitHub Publishing**: Can publish swimmies to PyPI independently

## Next Steps

1. **Create GitHub repository** for swimmies
2. **Push swimmies-repo** to GitHub  
3. **Replace local copy** with Git submodule
4. **Update documentation** with new repository URLs

This setup gives you the best of both worlds - independent library development with convenient workspace integration!
