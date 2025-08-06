# DNS Record Distribution Integration

This document describes the automatic DNS record distribution feature that integrates the swimmies library with Joyride DNS Service.

## Overview

The DNS record distribution feature automatically synchronizes DNS records across multiple Joyride DNS nodes discovered on the same network. This provides:

- **High Availability**: DNS records are distributed across multiple nodes
- **Automatic Discovery**: Nodes automatically find and connect to each other
- **Consistent Responses**: All nodes serve the same DNS records
- **Failure Recovery**: System continues operating even if some nodes fail

## Architecture

The system uses two main components from the swimmies library:

1. **Node Discovery**: UDP broadcast-based discovery of other DNS nodes on the local network
2. **SWIM Protocol**: Distributed membership management and DNS record synchronization

### Components

#### DNSSyncManager
- Main orchestrator for DNS record distribution
- Integrates swimmies discovery and SWIM protocol
- Manages local DNS records and synchronization
- Provides cluster status and statistics

#### Integration Points
- **DNS Server**: Receives synchronized records and serves DNS queries
- **Docker Monitor**: DNS records from Docker containers are distributed
- **Hosts Monitor**: DNS records from host files are distributed

## Configuration

The feature is controlled by environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DNS_SYNC` | `"true"` | Enable/disable DNS synchronization |
| `NODE_ID` | `"joyride-{pid}"` | Unique identifier for this node |
| `DISCOVERY_PORT` | `8889` | UDP port for node discovery |
| `SWIM_PORT` | `8890` | UDP port for SWIM protocol |

## Usage

### Starting with DNS Sync Enabled

```bash
# Enable DNS synchronization (default)
export ENABLE_DNS_SYNC=true
export NODE_ID=dns-node-1
export DISCOVERY_PORT=8889
export SWIM_PORT=8890

# Start Joyride DNS
python -m app.main
```

### Disabling DNS Sync

```bash
# Disable DNS synchronization
export ENABLE_DNS_SYNC=false

# Start Joyride DNS (single node mode)
python -m app.main
```

## API Endpoints

New endpoints for DNS cluster management:

### GET /dns/cluster
Returns DNS cluster status and node information.

**Response:**
```json
{
  "status": "success",
  "cluster": {
    "node_id": "dns-node-1",
    "running": true,
    "discovered_nodes": 2,
    "statistics": {
      "nodes_discovered": 2,
      "nodes_active": 2,
      "dns_records_synced": 15,
      "sync_operations": 3,
      "last_sync": "2025-08-04T10:30:00Z"
    },
    "nodes": [
      {
        "node_id": "dns-node-2",
        "ip_address": "192.168.1.101",
        "last_seen": "2025-08-04T10:29:45Z",
        "metadata": {"role": "dns-server", "swim_port": 8890}
      }
    ],
    "swim_cluster": {
      "alive_members": 2,
      "member_counts": {"alive": 2, "suspect": 0, "failed": 0, "left": 0},
      "dns_version": 5
    }
  }
}
```

### POST /dns/sync
Force immediate DNS record synchronization across the cluster.

**Response:**
```json
{
  "status": "success",
  "message": "DNS synchronization initiated"
}
```

## Web Interface

The status page now includes DNS cluster information when synchronization is enabled:

- **Node ID**: Unique identifier for this node
- **Running Status**: Whether DNS sync is active
- **Discovered Nodes**: Number of nodes found on the network
- **SWIM Alive Members**: Number of nodes in the SWIM cluster
- **Statistics**: Sync operations, records synced, last sync time
- **Cluster Nodes**: List of all discovered nodes with their roles

## How It Works

### Node Discovery Process

1. **Broadcast**: Each node broadcasts its presence via UDP
2. **Discovery**: Other nodes receive broadcasts and add discovered nodes
3. **SWIM Connection**: Nodes establish SWIM protocol connections
4. **Cluster Formation**: All nodes join a single SWIM cluster

### DNS Record Synchronization

1. **Local Changes**: When DNS records are added/removed locally
2. **SWIM Distribution**: Changes are distributed via SWIM gossip protocol
3. **Remote Updates**: Other nodes receive and apply changes
4. **Consistency**: All nodes maintain the same set of DNS records

### Failure Handling

1. **Node Failure Detection**: SWIM protocol detects failed nodes
2. **Automatic Recovery**: Remaining nodes continue serving DNS
3. **Rejoin Support**: Failed nodes can rejoin when they recover
4. **Data Consistency**: DNS records remain consistent across healthy nodes

## Examples

### Two-Node Setup

**Node 1:**
```bash
export NODE_ID=dns-primary
export HOSTIP=192.168.1.100
python -m app.main
```

**Node 2:**
```bash
export NODE_ID=dns-secondary  
export HOSTIP=192.168.1.101
python -m app.main
```

Both nodes will automatically discover each other and synchronize DNS records.

### Docker Container Integration

When Docker containers with `joyride.host.name` labels start:

1. **Local Detection**: Docker monitor detects container start
2. **DNS Record Creation**: Local DNS record is created
3. **Cluster Sync**: Record is distributed to all cluster nodes
4. **Global Availability**: All nodes can resolve the container hostname

### Monitoring

Check cluster health:
```bash
curl http://localhost:5000/dns/cluster
```

Force synchronization:
```bash
curl -X POST http://localhost:5000/dns/sync
```

View status page:
```bash
open http://localhost:5000/
```

## Troubleshooting

### Common Issues

**Nodes not discovering each other:**
- Check firewall settings for UDP ports 8889 and 8890
- Ensure nodes are on the same network segment
- Verify `HOSTIP` is set correctly for each node

**DNS records not syncing:**
- Check SWIM cluster status in `/dns/cluster` endpoint
- Force sync using `/dns/sync` endpoint
- Review logs for sync errors

**High network traffic:**
- Adjust `protocol_interval` for less frequent SWIM operations
- Reduce `gossip_factor` to limit message propagation

### Logging

Enable debug logging for detailed sync information:
```bash
export LOG_LEVEL=DEBUG
python -m app.main
```

Look for these log messages:
- `"DNS sync manager started successfully"`
- `"Discovered DNS node: {node_id} at {ip}"`
- `"SWIM member joined: {node_id}"`
- `"Received DNS sync with {count} records"`

## Performance Considerations

- **Network Overhead**: SWIM protocol generates periodic network traffic
- **Memory Usage**: Each node stores complete DNS record set
- **Convergence Time**: Changes propagate within seconds across the cluster
- **Scalability**: Tested with clusters up to 10 nodes

## Security Notes

- **Network Security**: UDP traffic is unencrypted (suitable for trusted networks)
- **Access Control**: No authentication between nodes (intended for internal use)
- **Isolation**: Use separate networks for different DNS clusters

## Future Enhancements

- Encryption for inter-node communication
- Authentication and authorization between nodes
- Cross-subnet discovery support
- DNS record conflict resolution policies
- Performance metrics and monitoring
