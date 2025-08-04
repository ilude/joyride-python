"""Container-related event definitions for the Joyride DNS Service."""

from datetime import datetime
from typing import Any, Dict, Optional

from ..core.event_base import JoyrideEvent


class JoyrideContainerEvent(JoyrideEvent):
    """Docker container lifecycle events."""
    
    def __init__(
        self,
        event_type: str,
        source: str,
        container_id: str,
        container_name: str,
        image: str,
        labels: Optional[Dict[str, str]] = None,
        networks: Optional[Dict[str, Any]] = None,
        ports: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize container event.
        
        Args:
            event_type: Type of container event
            source: Source component generating the event
            container_id: Docker container ID
            container_name: Container name
            image: Container image name
            labels: Container labels
            networks: Container network configuration
            ports: Container port mappings
            status: Container status
            data: Additional event data
            metadata: Additional event metadata
            timestamp: Event timestamp
        """
        event_data = data or {}
        event_data.update({
            "container_id": container_id,
            "container_name": container_name,
            "image": image,
            "labels": labels or {},
            "networks": networks or {},
            "ports": ports or {},
            "status": status
        })
        
        super().__init__(
            event_type=event_type,
            source=source,
            data=event_data,
            metadata=metadata,
            timestamp=timestamp
        )
    
    @property
    def container_id(self) -> str:
        """Get container ID."""
        return self.data["container_id"]
    
    @property
    def container_name(self) -> str:
        """Get container name."""
        return self.data["container_name"]
    
    @property
    def image(self) -> str:
        """Get container image."""
        return self.data["image"]
    
    @property
    def labels(self) -> Dict[str, str]:
        """Get container labels."""
        return self.data["labels"]
    
    @property
    def networks(self) -> Dict[str, Any]:
        """Get container networks."""
        return self.data["networks"]
    
    @property
    def ports(self) -> Dict[str, Any]:
        """Get container ports."""
        return self.data["ports"]
    
    @property
    def status(self) -> Optional[str]:
        """Get container status."""
        return self.data["status"]

    def _validate(self) -> None:
        """Validate container event data."""
        super()._validate()
        
        if not self.container_id:
            raise ValueError("Container ID cannot be empty")
        
        if not self.container_name:
            raise ValueError("Container name cannot be empty")
        
        if not self.image:
            raise ValueError("Container image cannot be empty")
