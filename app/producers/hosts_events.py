"""
Hosts file events for monitoring hosts file changes.
"""
from enum import Enum
from pathlib import Path
from typing import List, Optional

from app.joyride.events import Event


class HostsFileEventType(str, Enum):
    """Hosts file event types."""

    ENTRY_ADDED = "hosts.entry.added"
    ENTRY_REMOVED = "hosts.entry.removed"
    ENTRY_MODIFIED = "hosts.entry.modified"
    FILE_CHANGED = "hosts.file.changed"
    FILE_MODIFIED = "hosts.file.modified"
    FILE_CREATED = "hosts.file.created"
    FILE_DELETED = "hosts.file.deleted"
    FILE_BACKUP = "hosts.file.backup"
    BACKUP_CREATED = "hosts.backup.created"
    FILE_ERROR = "hosts.file.error"
    PARSE_ERROR = "hosts.parse.error"


class HostsEvent(Event):
    """Base class for hosts events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        hosts_event_type: HostsFileEventType,
        file_path,
        **kwargs,
    ):
        """Initialize hosts event."""
        self.hosts_event_type = hosts_event_type
        self.file_path = file_path

        # Extract event-specific parameters and add to data
        event_data = kwargs.pop("data", {})

        # Move all extra kwargs into the data dict
        for key, value in list(kwargs.items()):
            if key not in ["event_id", "timestamp", "metadata"]:
                event_data[key] = kwargs.pop(key)

        event_data.update(
            {
                "hosts_event_type": hosts_event_type.value,
                "file_path": str(file_path),
            }
        )

        super().__init__(
            event_type=event_type or hosts_event_type.value,
            source=source,
            data=event_data,
            **kwargs,
        )

    def _validate(self) -> None:
        """Validate hosts event data."""
        super()._validate()
        if not self.hosts_event_type:
            raise ValueError("hosts_event_type cannot be empty")
        if not self.file_path:
            raise ValueError("file_path cannot be empty")


class HostsEntryEvent(HostsEvent):
    """Hosts file entry event."""

    def __init__(
        self,
        hosts_event_type: HostsFileEventType,
        source: str,
        file_path,
        ip_address: str,
        hostnames: Optional[List[str]] = None,
        hostname: Optional[str] = None,
        **kwargs,
    ):
        """Initialize hosts entry event."""
        # Store the specific parameters
        self.ip_address = ip_address
        self.hostnames = hostnames or []

        # Handle hostname or hostnames parameter
        if hostname and hostname not in self.hostnames:
            self.hostnames.insert(0, hostname)

        super().__init__(
            event_type=hosts_event_type.value,
            source=source,
            hosts_event_type=hosts_event_type,
            file_path=file_path,
            ip_address=ip_address,
            hostnames=self.hostnames,
            hostname=self.hostnames[0] if self.hostnames else None,
            **kwargs,
        )

    @property
    def primary_hostname(self) -> Optional[str]:
        """Get the primary hostname."""
        return self.hostnames[0] if self.hostnames else None

    @property
    def is_localhost(self) -> bool:
        """Check if this is a localhost entry."""
        return self.ip_address in ("127.0.0.1", "::1", "localhost")


class HostsFileEvent(HostsEvent):
    """Hosts file event."""

    pass


class HostsFileModificationEvent(HostsEvent):
    """Hosts file modification event."""

    pass


class HostsFileChangeEvent(HostsEvent):
    """Hosts file change event."""

    pass


class HostsBackupEvent(HostsEvent):
    """Hosts file backup event."""

    pass


class HostsParseErrorEvent(HostsEvent):
    """Hosts file parse error event."""

    pass


class HostsFileEventProducer:
    """Producer for hosts file events."""

    def __init__(self):
        """Initialize the producer."""
        self.file_path = Path("/etc/hosts")

    def create_entry_event(
        self,
        event_type: HostsFileEventType,
        ip_address: str,
        hostnames: List[str],
        line_number: int = 0,
    ) -> HostsEntryEvent:
        """Create a hosts entry event."""
        return HostsEntryEvent(
            hosts_event_type=event_type,
            source="hosts_monitor",
            file_path=self.file_path,
            ip_address=ip_address,
            hostnames=hostnames,
            line_number=line_number,
        )
