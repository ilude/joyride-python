# Joyride DNS Service

A Python Flask microservice that provides dynamic DNS services by monitoring Docker container events. It automatically creates DNS records for containers with the `joyride.host.name` label, routing all traffic to the configured host IP address.

## Features

- 🐍 Python 3.12 with modern UV package management
- 🌐 Dynamic DNS server with automatic record management
- 🐳 Docker event monitoring for container lifecycle
- 🏷️ Label-based DNS registration (`joyride.host.name`)
- 📁 Static DNS records from hosts files (optional)
- 🔗 **Distributed DNS synchronization** - Automatic DNS record distribution across discovered nodes
- 🌙 Dark/light mode theme toggle on web interface
- 🔧 VS Code DevContainer with Docker-in-Docker support
- ⚙️ Configuration via environment variables and pyproject.toml
- 🏥 Health check endpoints for monitoring  
- 📊 Status web page with DNS records display and cluster information
- 🔒 Non-root user for security
- 🧪 Complete integration testing with pytest
- 📦 Integrated swimmies utility library with SWIM protocol

## Project Structure

```
joyride/
├── pyproject.toml              # Project config and dependencies
├── uv.lock                     # Locked dependencies
├── run.py                      # Application entry point
├── DEVELOPMENT.md              # Development guide
├── app/                        # Main application code
│   ├── main.py                 # Flask application
│   ├── dns_server.py           # DNS server implementation
│   ├── docker_monitor.py       # Docker event monitoring
│   ├── hosts_monitor.py        # Hosts file monitoring
│   ├── static/                 # CSS and static assets
│   └── templates/              # HTML templates
├── swimmies/                   # Git submodule - utility library
│   ├── pyproject.toml          # Library configuration
│   └── src/swimmies/           # Library source code
├── tests/                      # Test suite
│   ├── conftest.py             # Test configuration
│   ├── test_main.py            # Flask app tests
│   ├── test_docker_monitor.py  # Docker monitor tests
│   └── test_hosts_monitor.py   # Hosts monitor tests
├── hosts/                      # Example hosts files (optional)
├── Dockerfile                  # Production container image
├── docker-compose.yml          # Docker Compose configuration
└── Makefile                    # Build and development commands
```

## Quick Start

### Using UV (Recommended for Development)

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/ilude/joyride-python.git
cd joyride-python

# Install dependencies
uv sync --extra dev

# Run the application
uv run python run.py

# Access web interface at http://localhost:5000
# DNS server runs on port 5353 (UDP)
```

### Using VS Code DevContainer

1. Open the project in VS Code
2. Install the "Dev Containers" extension
3. Press `Ctrl+Shift+P` and run "Dev Containers: Reopen in Container"
4. VS Code will build and start the development container
### Using Docker Compose

```bash
# Start development container
docker-compose up --build

# Access web interface at http://localhost:5000
# DNS server runs on port 5353 (UDP)
```

### Development Commands

The project uses UV for modern Python package management:

```bash
# Install dependencies
uv sync --extra dev

# Run application
uv run python run.py

# Run tests
uv run pytest tests/ -v

# Code quality
uv run black app/ tests/ run.py
uv run isort app/ tests/ run.py  
uv run flake8 app/ tests/ run.py

# Update dependencies
uv lock --upgrade
```

See `DEVELOPMENT.md` for comprehensive development guide.

## How It Works

The Joyride DNS Service automatically creates DNS records from two sources:

### 1. Docker Container Monitoring
Automatically creates DNS records for Docker containers:

1. **Container Labeling**: Add `joyride.host.name=your.domain.com` label to containers
2. **Automatic Discovery**: Service monitors Docker events for container lifecycle
3. **DNS Record Creation**: Creates A records pointing to the configured host IP
4. **Dynamic Updates**: Automatically removes records when containers stop

### 2. Static Hosts Files (Optional)
Load DNS records from hosts files in a bind-mounted directory:

1. **Hosts Directory**: Mount a directory containing hosts files via Docker volume
2. **File Monitoring**: Service watches for changes to files in the directory
3. **Standard Format**: Uses `/etc/hosts` format for maximum compatibility
4. **Hidden File Exclusion**: Files starting with `.` are ignored for security
5. **Live Updates**: Automatically reloads when files are modified

### Example Container Usage

```bash
# Start a container with DNS registration
docker run -d \
  --label joyride.host.name=app.example.com \
  --name my-app nginx

# The DNS service will automatically create:
# app.example.com -> [HOSTIP]
```

### Example Hosts File Format

Create files in your hosts directory using standard `/etc/hosts` format:

```bash
# /path/to/hosts/internal.hosts
# Format: IP_ADDRESS  HOSTNAME [HOSTNAME...]

# Internal services
192.168.1.100    api.internal dashboard.internal
192.168.1.101    database.internal db.internal

# Development services  
10.0.0.10        dev-app.local app.local
```

### Using Hosts Files with Docker Compose

```yaml
services:
  joyride:
    # ... other configuration ...
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./hosts:/app/hosts:ro  # Mount hosts directory
    environment:
      - HOSTS_DIRECTORY=/app/hosts  # Enable hosts monitoring
```

## Configuration

Configure the service using environment variables in `.env` or through `pyproject.toml`:

```bash
# Flask Web Interface
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# DNS Server
DNS_PORT=53
DNS_BIND_ADDRESS=0.0.0.0

# Service Identity
SERVICE_NAME=Joyride DNS
ENVIRONMENT=development

# Host IP for DNS records (auto-detected if not set)
HOSTIP=192.168.1.100

# Hosts File Monitoring (optional)
HOSTS_DIRECTORY=/path/to/hosts
```

### Project Metadata

The project uses modern Python packaging with `pyproject.toml`:

- **License**: MIT
- **Python**: >=3.12
- **Dependencies**: Managed through UV with optional groups
- **Repository**: https://github.com/ilude/joyride-python
- **Library**: Includes swimmies utility library as Git submodule

## API Endpoints

### Web Interface
- `GET /` - Main status page showing DNS records (HTML)

### Health & Status
- `GET /health` - Simple health check (JSON)
- `GET /status` - Detailed system status (JSON)

### DNS Management
- `GET /dns/records` - Current DNS records (JSON)

### DNS Server
- UDP port 5353 (configurable) - Standard DNS queries

### Example Health Check Response
```json
{
  "status": "healthy",
  "service": "Joyride DNS",
  "version": "1.0.0",
  "timestamp": "2025-08-03T12:00:00.000000"
}
```

### Example DNS Records Response
```json
{
  "status": "success",
  "total_records": 2,
  "records": [
    {
      "hostname": "app.example.com",
      "ip_address": "192.168.1.100",
      "ttl": 300
    },
    {
      "hostname": "api.example.com", 
      "ip_address": "192.168.1.100",
      "ttl": 300
    }
  ]
}
```

## Development

### Prerequisites
- VS Code with Dev Containers extension
- Docker Desktop
- Python 3.12 (for local development)

### Development Workflow
1. Open project in VS Code DevContainer (includes Docker-in-Docker)
2. Run `make initialize` to set up environment
3. Make changes to the code
4. The Flask development server will automatically reload
5. Test your changes at http://localhost:5000
6. Run integration tests with `make test-docker`

### Running Tests
```bash
# Inside the dev container
make test

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_docker_monitor.py -v
```

### Code Quality
```bash
# Format code
make format

# Run linting
make lint

# Clean cache files
make clean
```

### Testing DNS Functionality

The devcontainer includes Docker-in-Docker support and dig utility for complete integration testing:

```bash
# Test Docker integration and DNS resolution
make test-docker

# Manual testing commands
# Test DNS resolution (dig is pre-installed in devcontainer)
dig @localhost app.example.com

# Test with a running container
docker run -d --label joyride.host.name=test.internal nginx
dig @localhost test.internal

# Check DNS records via API
curl http://localhost:5000/dns/records
```

## Deployment

### Production Deployment with Docker
1. Set environment variables in `.env` or use Docker environment
2. Build the production image: `docker build -t joyride-dns .`
3. Run with proper permissions and socket access:
   ```bash
   docker run -d \
     -p 5000:5000 -p 5353:5353/udp \
     -v /var/run/docker.sock:/var/run/docker.sock \
     --env HOSTIP=your.host.ip \
     --restart unless-stopped \
     joyride-dns
   ```

### Production Deployment with Docker Compose
1. Update environment variables in `.env`
2. Run: `docker-compose up -d`
3. Monitor with: `docker-compose logs -f`

### Kubernetes Deployment
For Kubernetes deployment, ensure:
- Service account with Docker socket access or CRI integration
- Proper RBAC permissions for container monitoring
- Network policies allowing DNS traffic on port 5353
- ConfigMap/Secret for environment variables

## Architecture

### Components
- **Flask Web App**: Status interface and API endpoints (port 5000)
- **DNS Server**: UDP DNS server for hostname resolution (port 5353)
- **Docker Monitor**: Background service monitoring container events
- **DNS Record Manager**: In-memory DNS record storage with callback system

### Data Flow
1. Docker containers start/stop with `joyride.host.name` labels
2. Docker Monitor detects events via Docker socket
3. DNS records created/removed pointing to `HOSTIP`
4. DNS queries resolved by embedded DNS server
5. Web interface displays current DNS records

## Security Features

- Non-root users in both development and production containers
- Minimal Alpine Linux base images for reduced attack surface
- Docker socket access limited to read-only container monitoring
- Environment-based configuration (no hardcoded secrets)
- Health checks for container orchestration
- Input validation for DNS queries and API requests

## DNS Record Distribution

Joyride DNS now supports automatic DNS record distribution across multiple nodes using the integrated swimmies library with SWIM protocol. This provides high availability and automatic failover capabilities.

**Key Features:**
- Automatic node discovery on local networks
- Distributed consensus using SWIM protocol
- Real-time DNS record synchronization
- Cluster health monitoring and status reporting
- Failure detection and recovery

For detailed information, see [DNS Sync Integration Documentation](docs/DNS_SYNC_INTEGRATION.md).

## Monitoring

The service includes comprehensive monitoring capabilities:
- Health check endpoint (`/health`) for load balancers
- Detailed status endpoint (`/status`) with service metrics  
- DNS record listing (`/dns/records`) for operational visibility
- **DNS cluster status** (`/dns/cluster`) for distributed deployments
- Docker healthcheck configuration in compose file
- Structured logging for centralized log management

## Troubleshooting

### Common Issues

**DNS not resolving:**
- Check that containers have `joyride.host.name` labels
- Verify `HOSTIP` environment variable is set correctly
- Ensure DNS server is bound to correct interface
- Test with `dig @localhost -p 5353 your.domain.com`

**Container events not detected:**
- Verify Docker socket is mounted: `/var/run/docker.sock`
- Check Docker daemon is running and accessible
- Review Docker monitor logs for connection errors

**DNS sync not working (distributed mode):**
- Check firewall settings for UDP ports 8889 and 8890
- Ensure nodes are on the same network segment
- Verify `HOSTIP` is set correctly for each node
- Use `/dns/cluster` endpoint to check cluster status

**Web interface not accessible:**
- Confirm Flask is bound to `0.0.0.0` not `127.0.0.1`
- Check port 5000 is not blocked by firewall
- Verify container port mapping is correct

### Logs
```bash
# Docker Compose logs
docker-compose logs -f joyride

# Container logs
docker logs <container-name>

# Test DNS functionality
make dns-status  # (in devcontainer)
```

## License

This project is provided as-is for educational and development purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Run `make test` and `make lint` to verify code quality
5. Submit a pull request with clear description

## Version Management

The project uses semantic versioning with git tags:
```bash
make version        # Show current version
make bump-patch     # Increment patch version (x.x.X)
make bump-minor     # Increment minor version (x.X.0) 
make bump-major     # Increment major version (X.0.0)
```
