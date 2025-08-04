"""
Core event base class for the Joyride DNS Service.

This module defines the fundamental JoyrideEvent class that all events
in the system inherit from, providing a consistent interface and immutable
event data structures.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JoyrideEvent(ABC):
    """
    Abstract base class for all events in the Joyride DNS Service.
    
    Implements the Command pattern for encapsulating event data and provides
    a consistent interface for all event types. All events are immutable
    after creation to prevent unintended modifications.
    
    Attributes:
        event_id: Unique identifier for this event instance
        event_type: String identifier for the event type
        timestamp: When the event was created
        source: Component or system that produced the event
        data: Event-specific data payload
        metadata: Additional context information
    """
    
    def __init__(
        self,
        event_type: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize a new event.
        
        Args:
            event_type: String identifier for the event type
            source: Component or system that produced the event
            data: Event-specific data payload
            metadata: Additional context information
            event_id: Unique identifier (auto-generated if not provided)
            timestamp: Event creation time (auto-generated if not provided)
        """
        self._event_id = event_id or str(uuid.uuid4())
        self._event_type = event_type
        self._timestamp = timestamp or datetime.now(timezone.utc)
        self._source = source
        self._data = data or {}
        self._metadata = metadata or {}
        
        # Validate required fields
        self._validate()
    
    @property
    def event_id(self) -> str:
        """Unique identifier for this event instance."""
        return self._event_id
    
    @property
    def event_type(self) -> str:
        """String identifier for the event type."""
        return self._event_type
    
    @property
    def timestamp(self) -> datetime:
        """When the event was created."""
        return self._timestamp
    
    @property
    def source(self) -> str:
        """Component or system that produced the event."""
        return self._source
    
    @property
    def data(self) -> Dict[str, Any]:
        """Event-specific data payload."""
        return self._data.copy()  # Return copy to prevent modification
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional context information."""
        return self._metadata.copy()  # Return copy to prevent modification
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the event data.
        
        Args:
            key: Data key to retrieve
            default: Default value if key not found
            
        Returns:
            Value from event data or default
        """
        return self._data.get(key, default)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the event metadata.
        
        Args:
            key: Metadata key to retrieve
            default: Default value if key not found
            
        Returns:
            Value from event metadata or default
        """
        return self._metadata.get(key, default)
    
    @abstractmethod
    def _validate(self) -> None:
        """
        Validate event data and raise ValueError if invalid.
        
        Concrete event classes should override this method to implement
        event-specific validation logic.
        
        Raises:
            ValueError: If event data is invalid
        """
        if not self._event_type:
            raise ValueError("event_type cannot be empty")
        if not self._source:
            raise ValueError("source cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary representation.
        
        Returns:
            Dictionary containing all event data
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "metadata": self.metadata,
        }
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.event_type}({self.event_id}) from {self.source}"
    
    def __repr__(self) -> str:
        """Developer representation of the event."""
        return (
            f"{self.__class__.__name__}("
            f"event_id='{self.event_id}', "
            f"event_type='{self.event_type}', "
            f"source='{self.source}', "
            f"timestamp={self.timestamp})"
        )
