---
description: "Makefile best practices for Joyride DNS Service build system"
applyTo: "**/Makefile"
---

# Makefile Development Standards

### Target Organization
- Use real file targets instead of `.PHONY` when possible
- Group related targets with comments
- Include help target with clear descriptions
- Use `@` prefix to suppress command echo for clean output

### Variable Management
- Export environment variables needed by child processes
- Use conditional assignment (`?=`) for defaults
- Detect platform and runtime automatically
- Define variables at top of file

### Development Targets
- `clean` - Remove generated files and caches
- `test` - Run test suites with coverage
- `lint` - Run code quality checks
- `format` - Apply code formatting
- `run` - Start application locally

### Background Process Management
- Use real PID file targets (e.g., `/tmp/service.pid`)
- Send SIGTERM for graceful shutdown
- Clean up PID files in cleanup targets
- Use `--no-print-directory` for nested make calls

### Example Patterns
```makefile
# Real file target for background services
/tmp/service.pid: .install-dev
	@FLASK_DEBUG=false python -m app.main &
	@sleep 2

# Graceful shutdown
stop-app:
	@if [ -f /tmp/service.pid ]; then \
		kill -TERM `cat /tmp/service.pid` 2>/dev/null || true; \
	fi

# Quiet output for commands
test-integration: /tmp/service.pid
	@docker run --rm nginx >/dev/null
	@$(MAKE) --no-print-directory stop-app
```

### DevContainer Integration
- Separate `.devcontainer/Makefile` for development-specific targets
- Include with `-include .devcontainer/Makefile`
- Use development-friendly paths and settings
