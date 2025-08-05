"""File-related event definitions for the Joyride DNS Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..event_base import JoyrideEvent


class JoyrideFileEvent(JoyrideEvent):
    """Hosts file change events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        file_path: str,
        operation: str,
        records: Optional[List[Dict[str, str]]] = None,
        file_size: Optional[int] = None,
        file_mtime: Optional[datetime] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize file event.

        Args:
            event_type: Type of file event
            source: Source component generating the event
            file_path: Path to the hosts file
            operation: File operation (created, modified, deleted, scanned)
            records: DNS records found in file
            file_size: File size in bytes
            file_mtime: File modification time
            data: Additional event data
            metadata: Additional event metadata
            timestamp: Event timestamp
        """
        event_data = data or {}
        event_data.update(
            {
                "file_path": file_path,
                "operation": operation,
                "records": records or [],
                "file_size": file_size,
                "file_mtime": file_mtime,
            }
        )

        super().__init__(
            event_type=event_type,
            source=source,
            data=event_data,
            metadata=metadata,
            timestamp=timestamp,
        )

    @property
    def file_path(self) -> str:
        """Get file path."""
        return self.data["file_path"]

    @property
    def operation(self) -> str:
        """Get file operation."""
        return self.data["operation"]

    @property
    def records(self) -> List[Dict[str, str]]:
        """Get DNS records."""
        return self.data["records"]

    @property
    def file_size(self) -> Optional[int]:
        """Get file size."""
        return self.data["file_size"]

    @property
    def file_mtime(self) -> Optional[datetime]:
        """Get file modification time."""
        return self.data["file_mtime"]

    def _validate(self) -> None:
        """Validate file event data."""
        super()._validate()

        if not self.file_path:
            raise ValueError("File path cannot be empty")

        if not self.operation:
            raise ValueError("File operation cannot be empty")

        # Validate file size if provided
        if self.file_size is not None and self.file_size < 0:
            raise ValueError("File size must be non-negative")
