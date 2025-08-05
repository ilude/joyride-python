# Joyride DNS Service

Dynamic DNS service that automatically creates DNS records for Docker containers with `joyride.host.name` labels and optionally from hosts files.

## Features

- **Docker Integration**: Automatic DNS records from container labels
- **Distributed Sync**: DNS record distribution across discovered nodes using SWIM protocol  
- **Static Records**: Load DNS records from hosts files
- **Web Interface**: Status dashboard with dark/light mode
- **API Endpoints**: Health checks and DNS record management

## Quick Start

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/ilude/joyride-python.git
cd joyride-python

# Using UV (recommended)
make install
make run

# Using Docker Compose
make up

# Access web interface: http://localhost:5000
# DNS server: port 5353 (UDP)
```

## Usage

### Docker Container Registration
```bash
docker run -d --label joyride.host.name=app.example.com nginx
# Creates DNS record: app.example.com -> [HOSTIP]
```

### Hosts Files (Optional)
```bash
# Mount directory with hosts files
make up

# hosts/example.hosts
192.168.1.100    api.internal dashboard.internal
```

### Multi-Node DNS Sync
```bash
# Node 1
export NODE_ID=dns-primary HOSTIP=192.168.1.100
make run

# Node 2  
export NODE_ID=dns-secondary HOSTIP=192.168.1.101
make run
# Nodes automatically discover and sync DNS records
```

## Configuration

Key environment variables:

```bash
# Service configuration
HOSTIP=192.168.1.100           # IP for DNS records (auto-detected if not set)
HOSTS_DIRECTORY=/app/hosts     # Optional hosts files directory

# DNS Sync (distributed mode)
ENABLE_DNS_SYNC=true           # Enable distributed sync
NODE_ID=dns-node-1             # Unique node identifier
DISCOVERY_PORT=8889            # Node discovery port
SWIM_PORT=8890                 # SWIM protocol port

# Flask/DNS ports (defaults: 5000, 5353)
FLASK_PORT=5000
DNS_PORT=5353
```

## API Endpoints

- `GET /` - Status dashboard
- `GET /health` - Health check
- `GET /status` - Detailed system status  
- `GET /dns/records` - Current DNS records
- `GET /dns/cluster` - Cluster status (distributed mode)
- `POST /dns/sync` - Force DNS synchronization

## Project Structure

```
joyride/
├── app/                        # Application code
│   ├── main.py                 # Flask application
│   ├── dns_server.py           # DNS server
│   ├── dns_sync_manager.py     # Distributed DNS sync
│   ├── docker_monitor.py       # Container monitoring
│   ├── hosts_monitor.py        # Hosts file monitoring
│   ├── static/                 # Web assets
│   └── templates/              # HTML templates
├── swimmies/                   # SWIM protocol library (git submodule)
├── tests/                      # Test suite
├── docs/                       # Documentation
├── hosts/                      # Example hosts files
├── pyproject.toml              # Project configuration
└── docker-compose.yml          # Container orchestration
```

## Development

```bash
# Install dependencies
make install

# Run tests
make test

# Code formatting
make format

# Linting
make lint

# Test DNS functionality
dig @localhost -p 5353 your.domain.com
```

## Distributed DNS Sync

Automatic DNS record distribution using SWIM protocol:

- **Node Discovery**: Nodes find each other via UDP broadcast
- **SWIM Protocol**: Distributed consensus and failure detection
- **Real-time Sync**: DNS records synchronized across all nodes
- **High Availability**: Service continues if nodes fail

See [DNS Sync Integration Documentation](docs/DNS_SYNC_INTEGRATION.md) for details.

## Troubleshooting

**DNS not resolving:**
- Verify containers have `joyride.host.name` labels
- Check `HOSTIP` environment variable
- Test: `dig @localhost -p 5353 your.domain.com`

**Container events not detected:**
- Ensure Docker socket is mounted: `/var/run/docker.sock`

**DNS sync issues (distributed mode):**
- Check firewall for UDP ports 8889, 8890
- Verify nodes on same network segment
- Check cluster status: `curl http://localhost:5000/dns/cluster`

## License

MIT
