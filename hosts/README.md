# Hosts File Usage Examples

This directory contains example hosts files that demonstrate how to use the Joyride DNS Service hosts file monitoring feature.

## Quick Start

1. **Enable hosts monitoring** by setting the `HOSTS_DIRECTORY` environment variable:
   ```bash
   export HOSTS_DIRECTORY=/path/to/your/hosts
   ```

2. **Mount the hosts directory** in your Docker container:
   ```yaml
   volumes:
     - ./hosts:/app/hosts:ro
   environment:
     - HOSTS_DIRECTORY=/app/hosts
   ```

3. **Create hosts files** using the standard `/etc/hosts` format in your mounted directory.

## File Format

Hosts files use the standard Linux `/etc/hosts` format:

```
# Comments start with #
IP_ADDRESS  HOSTNAME [ADDITIONAL_HOSTNAMES...]
```

### Examples

**Basic entries:**
```
192.168.1.100  api.internal
10.0.0.1       database.internal
```

**Multiple hostnames for one IP:**
```
192.168.1.100  api.internal api.local api.dev
```

**Production environment example:**
```
# Load balancers
192.168.100.10  lb1.prod.local lb-primary.prod.local
192.168.100.11  lb2.prod.local lb-secondary.prod.local

# Application servers
192.168.100.20  app1.prod.local
192.168.100.21  app2.prod.local
```

## Features

- **Live monitoring**: Files are automatically monitored for changes
- **Multiple files**: All files in the directory are loaded
- **Hidden file exclusion**: Files starting with `.` are ignored for security
- **Standard format**: Uses familiar `/etc/hosts` syntax
- **Error handling**: Invalid entries are logged and skipped
- **Comments supported**: Lines starting with `#` are ignored

## File Organization

You can organize your hosts files however makes sense for your environment:

```
hosts/
├── production.hosts     # Production services
├── development.hosts    # Development environment
├── internal.hosts       # Internal services
├── external.hosts       # External services
├── .gitignore          # Ignored (hidden file)
└── .DS_Store           # Ignored (hidden file)
```

**Files that are ignored:**
- Hidden files starting with `.` (e.g., `.gitignore`, `.DS_Store`, `.tmp`)
- This prevents accidental loading of system/metadata files
- For security and to avoid parsing non-hosts files

## Integration with Docker Labels

The hosts file feature works alongside Docker container monitoring. DNS records from both sources are combined:

- **Docker containers** with `joyride.host.name` labels → automatic registration
- **Hosts files** → static DNS records
- **Combined** → single DNS namespace

## API Endpoints

Check the status of hosts file monitoring:

- `GET /status` - Shows hosts monitor status and record count
- `GET /dns/records` - Lists all DNS records (Docker + hosts files)

## Troubleshooting

**No records loaded:**
- Check that `HOSTS_DIRECTORY` is set correctly
- Verify the directory exists and is readable
- Check file permissions (files should be readable by the service)

**Invalid entries:**
- Check the application logs for parsing errors
- Verify IP address format (must be valid IPv4)
- Ensure proper file format (IP followed by hostnames)

**Changes not detected:**
- File monitoring polls every 5 seconds by default
- Large files may take time to process
- Check that files are being modified, not just created

## Security Notes

- Mount hosts directory as read-only (`:ro`) for security
- Use non-privileged user for file ownership
- Validate IP addresses in your hosts files
- Consider file permissions and access controls
