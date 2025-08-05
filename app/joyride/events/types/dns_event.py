"""DNS-related event definitions for the Joyride DNS Service."""

from datetime import datetime
from typing import Any, Dict, Optional

from ..event import Event


class DNSEvent(Event):
    """Base class for DNS-related events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        record_name: str,
        record_type: str = "A",
        record_value: Optional[str] = None,
        ttl: int = 300,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize DNS event.

        Args:
            event_type: Type of DNS event
            source: Source component generating the event
            record_name: DNS record name (hostname)
            record_type: DNS record type (A, AAAA, CNAME, etc.)
            record_value: DNS record value (IP address, target, etc.)
            ttl: Time to live for the DNS record
            data: Additional event data
            metadata: Additional event metadata
            timestamp: Event timestamp
        """
        event_data = data or {}
        event_data.update(
            {
                "record_name": record_name,
                "record_type": record_type,
                "record_value": record_value,
                "ttl": ttl,
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
    def record_name(self) -> str:
        """Get DNS record name."""
        return self.data["record_name"]

    @property
    def record_type(self) -> str:
        """Get DNS record type."""
        return self.data["record_type"]

    @property
    def record_value(self) -> Optional[str]:
        """Get DNS record value."""
        return self.data["record_value"]

    @property
    def ttl(self) -> int:
        """Get DNS record TTL."""
        return self.data["ttl"]

    def _validate(self) -> None:
        """Validate DNS event data."""
        super()._validate()

        if not self.record_name:
            raise ValueError("DNS record name cannot be empty")

        if not self.record_type:
            raise ValueError("DNS record type cannot be empty")

        # Validate TTL is positive
        if self.ttl < 0:
            raise ValueError("DNS record TTL must be non-negative")
